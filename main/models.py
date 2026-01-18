from django.db import models
import uuid

# Create your models here.

class Room(models.Model):
    code = models.CharField(max_length=6, unique=True, db_index=True)

    players_count = models.PositiveSmallIntegerField()

    difficulty = models.PositiveSmallIntegerField()   # 1–5
    balance = models.PositiveSmallIntegerField()      # 1–5
    severity = models.PositiveSmallIntegerField()  # 1–5

    is_playing = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Room {self.code}"
    

class Player(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='players'
    )

    nickname = models.CharField(max_length=20, null=True, blank=True)

    seat = models.PositiveSmallIntegerField()
    is_alive = models.BooleanField(default=True)
    is_host = models.BooleanField(default=False)

    device_id = models.CharField(max_length=64) # ^ Get from frontend

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'seat')

    def __str__(self):
        return f"Player {self.seat} in {self.room.code}"
    

# & Все, что касается характеристик

class TraitType(models.TextChoices):
    BIO = 'bio', 'Био'
    PROFESSION = 'profession', 'Профессия'
    HEALTH = 'health', 'Здоровье'
    HOBBY = 'hobby', 'Хобби'
    FEAR = 'fear', 'Страх'
    CHARACTER = 'character', 'Характер'
    BACKGROUND = 'background', 'Прошлое'
    KNOWLEDGE = 'knowledge', 'Знание'
    ITEM = 'item', 'Предметы'


class Trait(models.Model):
    """Статичая модель карточки"""
    trait_type = models.CharField(
        max_length=16,
        choices=TraitType.choices
    )

    description = models.TextField()

    power = models.IntegerField(
        help_text="Отрицательное значение - что-то плохое. Положительное - что-то хорошее. От -10 до 10"
    )

    def __str__(self):
        return f"{self.description}"
    

class AssignedTrait(models.Model):
    """Модель для карточки, которая прикреплена к игроку"""
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='player_traits'
    )

    trait_type = models.CharField(
        max_length=16,
        choices=TraitType.choices
    )

    description = models.TextField()

    is_revealed = models.BooleanField(default=False)

    class Meta:
        ordering = ["trait_type"]


    def __str__(self):
        return f"{self.player} - {self.description}"
    

class ActionCard(models.Model):
    description = models.TextField()

    def __str__(self):
        return f"Action: {self.description}"


class ReactionCard(models.Model):
    description = models.TextField()

    def __str__(self):
        return f"Reaction: {self.description}"


class AssignedActionCard(models.Model):
    player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name='action_card'
    )
    card = models.ForeignKey(ActionCard, on_delete=models.CASCADE)
    description = models.TextField()
    is_used = models.BooleanField(default=False)


class AssignedReactionCard(models.Model):
    player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name='reaction_card'
    )
    card = models.ForeignKey(ReactionCard, on_delete=models.CASCADE)
    description = models.TextField()
    is_used = models.BooleanField(default=False)
    
# &

class ShelterDescription(models.Model):
    size = models.PositiveSmallIntegerField(help_text="От 1 до 3 (не кол-во мест!)")
    difficulty = models.PositiveSmallIntegerField(help_text="От 1 до 5 (чем больше - тем сложнее)")
    description = models.TextField()


class Shelter(models.Model):
    """Динамичная сущность - прикрепляется к игре"""

    room = models.OneToOneField(
        Room,
        on_delete=models.CASCADE,
        related_name='shelter'
    )

    capacity = models.PositiveSmallIntegerField()

    description = models.ForeignKey(
        ShelterDescription,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"Shelter for room {self.room.code}"
    

class Catastrophe(models.Model):
    severity = models.PositiveSmallIntegerField(help_text="От 1 до 5")
    title = models.CharField(max_length=255)
    description = models.TextField()


class RoomCatastrophe(models.Model):
    room = models.OneToOneField(
        Room,
        on_delete=models.CASCADE,
        related_name='room_catastrophe'
    )

    catastrophe = models.ForeignKey(
        Catastrophe,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.room.code} - {self.catastrophe.title}"

