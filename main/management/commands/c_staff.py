from django.core.management import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from main.models import (
    Trait,
    ShelterDescription,
    Catastrophe,
    Player,
    AssignedTrait,
    ActionCard,
    ReactionCard,
    AssignedActionCard,
    AssignedReactionCard,
    Room,
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        username = "editor"
        email = "editor@gmail.com"
        password = "S8!do?iF4_"

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"User '{username}' already exists.")
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = False
        user.save()

        # Create group
        group, _ = Group.objects.get_or_create(
            name="Main App Editors (no Room)"
        )

        editable_models = [
            Trait,
            ShelterDescription,
            Catastrophe,
            Player,
            AssignedTrait,
            ActionCard,
            ReactionCard,
            AssignedActionCard,
            AssignedReactionCard,
        ]

        permissions = []

        for model in editable_models:
            content_type = ContentType.objects.get_for_model(model)
            model_perms = Permission.objects.filter(
                content_type=content_type,
                codename__in=[
                    f"add_{model._meta.model_name}",
                    f"change_{model._meta.model_name}",
                    f"view_{model._meta.model_name}",
                ],
            )
            permissions.extend(model_perms)

        group.permissions.set(permissions)
        user.groups.add(group)

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user '{username}' created (Room excluded)."
            )
        )
