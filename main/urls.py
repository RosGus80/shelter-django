from django.urls import path
from main.views import (
    RoomCreateAPIView,
    RoomRetrieveAPIView,
    RoomRestartAPIView,
    PlayerRetrieveAPIView,
    PlayerUpdateAPIView,
    JoinRoomAPIView,
    RevealTraitAPIView,
    StartGameAPIView,
    LeaveRoomAPIView,
    UseActionCardView,
    UseReactionCardView,
    PlayerByDeviceView,
)

app_name = "main"

urlpatterns = [
    path("rooms/", RoomCreateAPIView.as_view(), name="room-create"),
    path("rooms/<str:code>/", RoomRetrieveAPIView.as_view(), name="room-retrieve"),
    path(
        "rooms/<str:code>/restart/", RoomRestartAPIView.as_view(), name="room-restart"
    ),
    path("rooms/<str:code>/join/", JoinRoomAPIView.as_view(), name="join-room"),
    path("rooms/<str:code>/start/", StartGameAPIView.as_view(), name="start-game"),
    path("rooms/<str:code>/leave/", LeaveRoomAPIView.as_view(), name="leave-room"),
    path("players/<int:pk>/", PlayerRetrieveAPIView.as_view(), name="player-retrieve"),
    path(
        "players/<int:player_id>/traits/<int:trait_id>/reveal/",
        RevealTraitAPIView.as_view(),
        name="reveal-trait",
    ),
    path(
        "rooms/<str:code>/player/",
        PlayerUpdateAPIView.as_view(),
        name="player-update",
    ),
    path("action-cards/<int:pk>/use/", UseActionCardView.as_view()),
    path("reaction-cards/<int:pk>/use/", UseReactionCardView.as_view()),

    path("players/by-device/", PlayerByDeviceView.as_view()),
]
