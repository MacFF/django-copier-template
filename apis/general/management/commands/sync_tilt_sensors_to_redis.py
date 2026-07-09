"""
Management command: sync_tilt_sensors_to_redis

Bulk-syncs all active Soil Tilt sensor keys to Redis Sets per device.
Go realtime service reads these Sets to know which sensor_keys
require voltage→degree calculation before publishing to WebSocket channel.

Redis key   : tilt_sensors:{device_id}
Redis type  : Set
Redis value : e.g. {"tilt_1", "tilt_2", "tilt_3"}

Run this once on initial deploy or after Redis flush:
    uv run manage.py sync_tilt_sensors_to_redis
"""

import logging

from django.core.management.base import BaseCommand

from apis.device.services import SensorService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync all Soil Tilt sensor keys to Redis Sets per device (for Go realtime service)"

    def handle(self, *args, **options):
        self.stdout.write("Syncing Soil Tilt sensor keys to Redis…")

        synced_devices = SensorService.bulk_sync_tilt_sensors_to_redis()

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — tilt sensor keys synced for {synced_devices} device(s)."
            )
        )
