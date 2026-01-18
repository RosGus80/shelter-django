import random
from main.models import Catastrophe, RoomCatastrophe


def create_catastrophe(room):
    qs = Catastrophe.objects.filter(
        severity__lte=room.catastrophe,
    )

    if not qs.exists():
        raise RuntimeError("No catastrophes available for given severity")

    catastrophe = random.choice(list(qs))

    return RoomCatastrophe.objects.create(
        room=room,
        catastrophe=catastrophe
    )