import math
import random
from main.models import Shelter, ShelterDescription


def calculate_shelter_size(players_count: int) -> int:
    """Для "размера" описания для бункера (исключительно для иммерсивности)"""
    half = players_count // 2

    if half <= 3:
        return 1
    elif half <= 6:
        return 2
    else:
        return 3
    

def calculate_shelter_cap(players_count: int) -> int:
    if players_count // 2 == 1:
        return 2
    else:
        return players_count // 2
    

def create_shelter(room):
    """Выбирает случайный подходящий бункер"""
    size = calculate_shelter_size(room.players_count)

    capacity = calculate_shelter_cap(room.players_count)

    descriptions = ShelterDescription.objects.filter(
        size=size,
        difficulty__lte=room.difficulty
    )

    if not descriptions.exists():
        raise RuntimeError("No shelter descriptions for given size/difficulty")

    description = random.choice(list(descriptions))

    return Shelter.objects.create(
        room=room,
        capacity=capacity,
        description=description
    )
