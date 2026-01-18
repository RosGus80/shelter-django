from rest_framework import serializers
from .models import (
    Room,
    Player,
    AssignedTrait,
    Shelter,
    RoomCatastrophe,
    Catastrophe,
    AssignedActionCard,
    AssignedReactionCard,
)


class AssignedTraitSerializer(serializers.ModelSerializer):
    trait_type_display = serializers.CharField(
        source="get_trait_type_display", read_only=True
    )

    class Meta:
        model = AssignedTrait
        fields = (
            "pk",
            "trait_type",
            "trait_type_display",
            "description",
            "is_revealed",
        )


class AssignedActionCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssignedActionCard
        fields = ("pk", "description", "is_used")


class AssignedReactionCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssignedReactionCard
        fields = ("pk", "description", "is_used")


class PlayerSerializer(serializers.ModelSerializer):
    player_traits = AssignedTraitSerializer(many=True, read_only=True)
    action_card = AssignedActionCardSerializer(read_only=True)
    reaction_card = AssignedReactionCardSerializer(read_only=True)

    class Meta:
        model = Player
        fields = (
            "id",
            "seat",
            "device_id",
            "is_host",
            "is_alive",
            "nickname",
            "player_traits",
            "action_card",
            "reaction_card",
        )
        read_only_fields = (
            "id",
            "seat",
            "device_id",
            "is_host",
            "is_alive",
            "player_traits",
            "action_card",
            "reaction_card",
        )


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ("pk", "capacity", "description")


class CatastropheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catastrophe
        fields = (
            "id",
            "title",
            "description",
            "severity",
        )


class RoomCatastropheSerializer(serializers.ModelSerializer):
    catastrophe = CatastropheSerializer(read_only=True)

    class Meta:
        model = RoomCatastrophe
        fields = ("pk", "catastrophe")


class RoomRetrieveSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    shelter = ShelterSerializer(read_only=True)
    room_catastrophe = RoomCatastropheSerializer(read_only=True)

    class Meta:
        model = Room
        fields = (
            "code",
            "players_count",
            "difficulty",
            "balance",
            "severity",
            "is_playing",
            "players",
            "shelter",
            "room_catastrophe",
        )


class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = (
            "players_count",
            "difficulty",
            "balance",
            "severity",
        )

    def validate_players_count(self, value):
        if not 4 <= value <= 30:
            raise serializers.ValidationError("Players count must be between 4 and 30.")

        return value

    def validate(self, attrs):
        for field in ("difficulty", "balance", "severity"):
            if not 1 <= attrs[field] <= 5:
                raise serializers.ValidationError(f"{field} must be between 1 and 5.")
        return attrs
