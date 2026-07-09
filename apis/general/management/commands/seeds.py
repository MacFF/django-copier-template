import os
from django.core.management import BaseCommand, call_command

from {{project_slug}}.base.functions import strtobool


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running seeds.."))
        call_command("system_seed")
        call_command("sensor_seed")
        call_command("sync_sensor_range_to_redis")
        call_command("sync_tilt_sensors_to_redis")
        self.stdout.write(self.style.SUCCESS("All seeds done."))
