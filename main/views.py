from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny

from django.db.models import Q
from main.models import Room, Player, RoomCatastrophe, Shelter, AssignedTrait, AssignedActionCard, AssignedReactionCard
from main.serializers import (
    RoomCreateSerializer,
    RoomRetrieveSerializer,
    PlayerSerializer,
)
from main.utils import generate_room_code
from main.services.draw_content import draw_game_content

from datetime import timedelta


STALE_ROOM_DAYS = 7


# & Комнаты


class RoomCreateAPIView(generics.CreateAPIView):
    serializer_class = RoomCreateSerializer
    queryset = Room.objects.all()

    authentication_classes = []
    permission_classes = [AllowAny]


    def perform_create(self, serializer, code: str):
        """
        Actually creates the room and draws content.
        """
        room_data: dict[str, object] = dict(serializer.validated_data)
        room = Room.objects.create(code=code, **room_data)
        draw_game_content(room)
        return room

    def create(self, request, *args, **kwargs):
        """
        Override create to:
        - generate unique room code
        - create room with that code
        - draw content
        - return fully serialized room data
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = generate_room_code()
        while Room.objects.filter(code=code).exists():
            code = generate_room_code()

        room = self.perform_create(serializer, code=code)

        output_serializer = RoomRetrieveSerializer(room)

        headers = self.get_success_headers(serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class RoomRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomRetrieveSerializer
    lookup_field = "code"


class StartGameAPIView(APIView):
    def post(self, request, code):
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND
            )

        device_id = request.data.get("device_id")
        if not device_id:
            return Response(
                {"detail": "device_id required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            player = Player.objects.get(room=room, device_id=device_id)
        except Player.DoesNotExist:
            return Response(
                {"detail": "Player not found in this room."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not player.is_host:
            return Response(
                {"detail": "Only the host can start the game."},
                status=status.HTTP_403_FORBIDDEN,
            )

        room.is_playing = True
        room.save()

        return Response({"detail": "Game started."}, status=status.HTTP_200_OK)


class RoomRestartAPIView(APIView):
    def post(self, request, code):
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Room not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_players = (
            Player.objects
            .filter(room=room)
            .values("seat", "device_id", "nickname", "is_host")
        )

        player_snapshot = {
            p["seat"]: {
                "device_id": p["device_id"],
                "nickname": p["nickname"],
                "is_host": p["is_host"],
            }
            for p in old_players
            if p["device_id"]
        }

        Player.objects.filter(room=room).delete()
        Shelter.objects.filter(room=room).delete()
        RoomCatastrophe.objects.filter(room=room).delete()

        draw_game_content(room)

        for player in Player.objects.filter(room=room):
            snapshot = player_snapshot.get(player.seat)
            if snapshot:
                player.device_id = snapshot["device_id"]
                player.nickname = snapshot["nickname"]
                player.is_host = snapshot["is_host"]
                player.save(update_fields=["device_id", "nickname", "is_host"])

        room.is_playing = False
        room.save(update_fields=["is_playing"])

        serializer = RoomRetrieveSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)

# & Игроки


class PlayerRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class PlayerUpdateAPIView(generics.UpdateAPIView):
    serializer_class = PlayerSerializer
    queryset = Player.objects.all()
    http_method_names = ["patch"]

    def get_object(self):
        code = self.kwargs["code"]
        device_id = self.request.data.get("device_id")

        if not device_id:
            raise NotFound("device_id required")

        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            raise NotFound("Room not found")

        player = Player.objects.filter(room=room, device_id=device_id).first()

        if not player:
            raise NotFound("Player not found")

        return player


class JoinRoomAPIView(APIView):
    def post(self, request, code):
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Room not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        device_id = request.data.get("device_id")
        if not device_id:
            return Response(
                {"detail": "device_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        player = Player.objects.filter(room=room, device_id=device_id).first()
        if player:
            return Response(PlayerSerializer(player).data)

        existing_player = (
            Player.objects
            .filter(device_id=device_id)
            .exclude(room=room)
            .select_related("room")
            .first()
        )

        if existing_player:
            return Response(
                {
                    "detail": "Device already joined another room",
                    "room_code": existing_player.room.code,
                },
                status=status.HTTP_409_CONFLICT,
            )

        unassigned_player = (
            Player.objects
            .filter(room=room)
            .filter(Q(device_id__isnull=True) | Q(device_id=""))
            .order_by("seat")
            .first()
        )

        if not unassigned_player:
            return Response(
                {"detail": "Room is full"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unassigned_player.device_id = device_id
        unassigned_player.save()

        return Response(PlayerSerializer(unassigned_player).data)


class LeaveRoomAPIView(APIView):
    def post(self, request, code):
        # Delete stale rooms (>7 days old)
        stale_time = timezone.now() - timedelta(days=7)
        Room.objects.filter(updated_at__lt=stale_time).delete()

        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"detail": "device_id required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            player = Player.objects.get(room=room, device_id=device_id)
        except Player.DoesNotExist:
            return Response({"detail": "Player not found in this room."}, status=status.HTTP_404_NOT_FOUND)

        # Remove player from room
        player.device_id = ""
        player.save(update_fields=["device_id"])

        if player.is_host:
            room.delete()
            return Response(
                {"detail": "Host left the room. Room was empty and deleted."},
                status=status.HTTP_200_OK,
            )

        # Delete the room if no players have a device_id
        active_players = Player.objects.filter(room=room).exclude(Q(device_id="") | Q(device_id__isnull=True))
        if not active_players.exists():
            room.delete()
            return Response(
                {"detail": "Left the room. Room was empty and deleted."},
                status=status.HTTP_200_OK,
            )

        return Response({"detail": "Left the room."}, status=status.HTTP_200_OK)
    

class RevealTraitAPIView(APIView):
    def post(self, request, player_id, trait_id):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response(
                {"detail": "device_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            player = Player.objects.get(pk=player_id)
        except Player.DoesNotExist:
            return Response(
                {"detail": "Player not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if player.device_id != device_id:
            return Response(
                {"detail": "You can only reveal your own traits"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            trait = AssignedTrait.objects.get(pk=trait_id, player=player)
        except AssignedTrait.DoesNotExist:
            return Response(
                {"detail": "Trait not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if trait.is_revealed:
            return Response(
                {"detail": "Trait already revealed"}, status=status.HTTP_200_OK
            )

        trait.is_revealed = True
        trait.save(update_fields=["is_revealed"])

        return Response(
            {
                "trait_id": trait.pk,
                "is_revealed": trait.is_revealed,
            },
            status=status.HTTP_200_OK,
        )


class UseActionCardView(APIView):
    def post(self, request, pk):
        card = get_object_or_404(AssignedActionCard, pk=pk)

        if card.is_used:
            return Response(
                {"detail": "Action card already used"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        card.is_used = True
        card.save(update_fields=["is_used"])

        return Response({"status": "ok"})


class UseReactionCardView(APIView):
    def post(self, request, pk):
        card = get_object_or_404(AssignedReactionCard, pk=pk)

        if card.is_used:
            return Response(
                {"detail": "Reaction card already used"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        card.is_used = True
        card.save(update_fields=["is_used"])

        return Response({"status": "ok"})


class PlayerByDeviceView(APIView):
    def post(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"room": None})

        player = (
            Player.objects
            .filter(device_id=device_id, room__is_playing=True)
            .select_related("room")
            .first()
        )

        if not player:
            return Response({"room": None})

        return Response({
            "room": player.room.code
        })