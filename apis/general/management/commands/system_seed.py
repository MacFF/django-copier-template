import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, call_command

from apis.authentication.models import DeviceToken
from {{project_slug}}.base.models import get_system_user


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running system seed..."))
        self.seed_system_user()
        self.seed_superuser()
        self.seed_device_token_superuser()
        self.stdout.write(self.style.SUCCESS("system seeds done."))

    def seed_system_user(self):
        # Create System User (can't login)
        if not User.objects.filter(email="system@mail.com").exists():
            user = User.objects.create(
                username="system@mail.com",
                email="system@mail.com",
                first_name="System",
                is_active=False,
            )
            user.set_unusable_password()
            user.save()
    
    def seed_superuser(self):
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write(self.style.NOTICE('Creating superuser...'))
            email = "superadmin@admin.com"
            password = "1234"
            User.objects.create_superuser(
                username=email,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            self.stdout.write(self.style.WARNING(f'  email   : {email}'))
            self.stdout.write(self.style.WARNING(f'  password: {password}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser already exists. ({superuser.username}) Skipping creation.'))
    
    def seed_device_token_superuser(self):
        plain_token = secrets.token_urlsafe(32)
        sys_user = get_system_user()

        _, created = DeviceToken.objects.get_or_create(
            mqtt_topic="swd/phangan/#",
            token=plain_token,
            is_superuser=True,
            created_by=sys_user,
            updated_by=sys_user,
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Device-Token Superuser created successfully"))
        else:
            self.stdout.write(self.style.SUCCESS("Device-Token already created."))
