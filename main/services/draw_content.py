import random
from django.utils import timezone

from main.models import Player, Trait, AssignedTrait, Shelter, ShelterDescription, RoomCatastrophe, Catastrophe, TraitType, ActionCard, ReactionCard, AssignedActionCard, AssignedReactionCard

from main.services.bio_gen import generate_bio
from main.services.shelter import calculate_shelter_size, calculate_shelter_cap


# * Суммарная сила персонажей +- разброс - таблицы от уровня сложности и баланса
DIFFICULTY_TO_POWER = {1: 50, 2: 30, 3: 15, 4: 5, 5: -10}
BALANCE_TO_DEV = {1: 25, 2: 20, 3: 15, 4: 10, 5: 5}


def draw_player_cards(player):
    all_action_cards = list(ActionCard.objects.all())
    all_reaction_cards = list(ReactionCard.objects.all())

    if all_action_cards:
        card = random.choice(all_action_cards)
        AssignedActionCard.objects.create(player=player, description=card.description, card=card)
    if all_reaction_cards:
        card = random.choice(all_reaction_cards)
        AssignedReactionCard.objects.create(player=player, description=card.description, card=card)


def draw_player_traits(player, difficulty, balance):
    """
    Draws traits for a single player
    - Always one trait per type
    - Tries to keep total power around target +- dev
    """

    bio_data = generate_bio()
    AssignedTrait.objects.create(
        player=player,
        trait_type=TraitType.BIO,
        description=f"{bio_data['age']} лет, {bio_data['gender']}, {bio_data['orientation']}",
        is_revealed=False
    )

    trait_types = [
        TraitType.PROFESSION,
        TraitType.HEALTH,
        TraitType.HOBBY,
        TraitType.FEAR,
        TraitType.CHARACTER,
        TraitType.BACKGROUND,
        TraitType.KNOWLEDGE,
        TraitType.ITEM,
    ]

    target = DIFFICULTY_TO_POWER[difficulty]
    dev = BALANCE_TO_DEV[balance]

    assigned_traits = []
    assigned_power = 0

    traits_by_type = {t: list(Trait.objects.filter(trait_type=t)) for t in trait_types}

    for t_type in trait_types:
        pool = traits_by_type[t_type]
        if not pool:
            continue

        remaining_power = target - assigned_power

        suitable = [tr for tr in pool if
                    (remaining_power >= 0 and tr.power <= remaining_power + 5) or
                    (remaining_power < 0 and tr.power >= remaining_power - 5)]

        if not suitable:
            suitable = pool

        trait = random.choice(suitable)
        assigned_traits.append(trait)
        assigned_power += trait.power

    all_non_bio_traits = list(Trait.objects.exclude(trait_type=TraitType.BIO))
    random.shuffle(all_non_bio_traits)

    adjustment_attempts = 0
    while not (target - dev <= assigned_power <= target + dev) and adjustment_attempts < 20:
        adjustment_attempts += 1
        for trait in all_non_bio_traits:
            if trait.trait_type in [t.trait_type for t in assigned_traits]:
                continue

            potential_power = assigned_power + trait.power
            if abs(target - potential_power) < abs(target - assigned_power):
                assigned_traits.append(trait)
                assigned_power = potential_power
                break
        else:
            break

    for trait in assigned_traits:
        AssignedTrait.objects.create(
            player=player,
            trait_type=trait.trait_type,
            description=trait.description,
            is_revealed=False
        )


def draw_game_content(room):
    """
    Случайно собирает подходящий контент для комантыЖ
    - Игроки (персонажи и пустое место для подключения к ним)
    - Био хар-ки, другие хар-ки
    - Бункер
    - Катастрфоа
    """

    players = []

    # ! Первый подключившийся игрок - всегда хост, подключение должно проихойти при создании комнаты
    for seat in range(1, room.players_count + 1):
        player = Player.objects.create(
            room=room,
            seat=seat,
            is_host=(seat == 1),
            device_id=""
        )
        players.append(player)

    for player in players:
        draw_player_cards(player)
        draw_player_traits(player, room.difficulty, room.balance)

    shelter_size = calculate_shelter_size(room.players_count)
    capacity = calculate_shelter_cap(room.players_count)

    descriptions = list(
        ShelterDescription.objects.filter(
            size=shelter_size,
            difficulty__lte=room.difficulty
        )
    )

    if not descriptions:
        raise RuntimeError(
            f"No shelter descriptions for size={shelter_size}, difficulty≤{room.difficulty}"
        )

    shelter_description = random.choice(descriptions)

    Shelter.objects.create(
        room=room,
        capacity=capacity,
        description=shelter_description
    )

    catastrophes = list(
        Catastrophe.objects.filter(
            severity__lte=room.severity
        )
    )

    if not catastrophes:
        raise RuntimeError(
            f"No catastrophes for severity≤{room.room_catastrophe}"
        )

    catastrophe = random.choice(catastrophes)

    RoomCatastrophe.objects.create(
        room=room,
        catastrophe=catastrophe
    )

    room.started_at = timezone.now()
    room.save()
