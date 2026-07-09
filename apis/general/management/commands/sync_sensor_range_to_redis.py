"""
Management command: sync_sensor_range_to_redis

Bulk-syncs all active SensorRangeConfigs AND device sensor-key Sets to Redis.
Run this once after deploy or when Redis is flushed.

Usage:
    uv run manage.py sync_sensor_range_to_redis
"""

import logging

from django.core.management.base import BaseCommand

from apis.device.models import Device, Sensor
from apis.device.services import DeviceService, SensorService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync all SensorRangeConfigs and device sensor keys to Redis (iot DB)"

    def handle(self, *args, **options):
        # # ── 1. Sync device sensor-key Sets ─────────────────────────────
        # devices = Device.objects.filter(deleted__isnull=True)
        # self.stdout.write(f"Syncing sensor keys for {devices.count()} device(s)…")
        # for device in devices:
        #     DeviceService.sync_device_sensors_to_redis(device)

        # ── 2. Bulk-sync SensorRangeConfig Hashes via Pipeline ─────────
        sensors_qs = Sensor.objects.filter(deleted__isnull=True, is_active=True)
        total = sensors_qs.count()
        self.stdout.write(f"Bulk-syncing range configs for {total} sensor(s) via pipeline…")

        synced = SensorService.bulk_sync_sensor_ranges_to_redis(sensors_qs)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {synced}/{total} sensor(s) had range config and were synced to Redis."
            )
        )
