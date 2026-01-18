from django.core.management import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create a default superuser with hardcoded credentials using Django's default User model"

    def handle(self, *args, **options):
        username = "admin"
        email = "r@gmail.com"
        password = "PassOne1"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
