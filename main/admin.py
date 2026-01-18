from django.contrib import admin
from main.models import Trait, ShelterDescription, Catastrophe, Room, Player, AssignedTrait, ActionCard, ReactionCard, AssignedActionCard, AssignedReactionCard

# Register your models here.

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('code', 'pk')


@admin.register(ActionCard)
class ActionCardAdmin(admin.ModelAdmin):
    list_display = ('pk', )


@admin.register(ReactionCard)
class ReactionCardAdmin(admin.ModelAdmin):
    list_display = ('pk', )


@admin.register(Trait)
class TraitAdmin(admin.ModelAdmin):
    list_display = ('description', 'trait_type', 'power')
    list_filter = ('trait_type', 'power')
    search_fields = ('description',)
    ordering = ('trait_type', 'power')


@admin.register(ShelterDescription)
class ShelterDescriptionAdmin(admin.ModelAdmin):
    list_display = ('description', 'size', 'difficulty')
    list_filter = ('size', 'difficulty')
    search_fields = ('description',)
    ordering = ('size', 'difficulty')


@admin.register(Catastrophe)
class CatastropheAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'description')
    list_filter = ('severity',)
    search_fields = ('title', 'description')
    ordering = ('severity',)
