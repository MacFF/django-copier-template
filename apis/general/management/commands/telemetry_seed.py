"""
Mock telemetry seed for device: 26-6C-0E-F4-F9-23
Generates 1 year of data ending at today (UTC)

Sensor intervals:
  rainfall          → every 5 minutes (accumulating counter with occasional resets)
  air_temp          → every 5 seconds
  air_humidity      → every 5 seconds
  soil_moisture_1,2,3 → every 5 seconds
  soil_temp_1,2,3   → every 5 seconds
  tilt_1_x, tilt_1_y, tilt_2, tilt_3_x, tilt_3_y → every 5 seconds

Uses PostgreSQL COPY (via copy_expert) for maximum insert speed.

Usage:
  uv run manage.py telemetry_seed
"""
import io
import random
from datetime import datetime, timedelta, timezone

from django.core.management import BaseCommand
from django.db import connection


DEVICE_ID = "26-6C-0E-F4-F9-23"

# Regular sensors: (sensor_key, interval_seconds, base_value, amplitude, min_val, max_val)
REGULAR_SENSORS = [
    ("air_temp",       5,  26.24, 3.0,   10.0, 42.0),
    ("air_humidity",   5,  26.76, 15.0,  10.0, 95.0),
    ("soil_moisture_1", 5, 87.72, 5.0,   60.0, 100.0),
    ("soil_temp_1",    5,  24.68, 2.0,   15.0, 35.0),
    ("soil_moisture_2", 5, 87.04, 5.0,   60.0, 100.0),
    ("soil_temp_2",    5,  24.54, 2.0,   15.0, 35.0),
    ("soil_moisture_3", 5, 89.58, 5.0,   60.0, 100.0),
    ("soil_temp_3",    5,  24.07, 2.0,   15.0, 35.0),
    ("tilt_1_x",       5,  1.42,  0.15,   -2,  2),
    ("tilt_1_y",       5,  0.12,  0.15,   -2,  2),
    ("tilt_2",         5,  0.76,  0.3,   -2,  2),
    ("tilt_3_x",       5,  0.96,  0.2,   -2,  2),
    ("tilt_3_y",       5,  1.26,  0.15,   -2,  2),
]

COPY_SQL = """
    COPY telemetry (time, server_time, device_id, sensor_key, value)
    FROM STDIN WITH (FORMAT TEXT, DELIMITER '\t')
"""


def _generate_sensor_tsv(sensor_key: str, interval_sec: int, base: float, amp: float,
                         min_val: float, max_val: float, start: datetime, end: datetime) -> io.StringIO:
    """
    Generate data for a single regular sensor.
    """
    buf = io.StringIO()
    current = start
    value = base + random.uniform(-amp / 2, amp / 2)

    while current <= end:
        value += random.uniform(-amp * 0.05, amp * 0.05)
        value = max(min_val, min(max_val, value))
        server_time = current + timedelta(milliseconds=random.randint(10, 500))

        buf.write(
            f"{current.isoformat()}\t"
            f"{server_time.isoformat()}\t"
            f"{DEVICE_ID}\t"
            f"{sensor_key}\t"
            f"{round(value, 2)}\n"
        )
        current += timedelta(seconds=interval_sec)

    buf.seek(0)
    return buf


def _generate_rainfall_tsv(start: datetime, end: datetime) -> io.StringIO:
    """
    Generate rainfall accumulation data (counter with periodic resets).
    Interval: every 5 minutes
    """
    buf = io.StringIO()
    current = start
    counter = 4582.48
    reset_chance_per_day = 1.0 / 180.0

    while current <= end:
        if random.random() < reset_chance_per_day:
            counter = random.uniform(0.0, 100.0)
        else:
            counter += random.uniform(0.5, 2.5)

        server_time = current + timedelta(milliseconds=random.randint(10, 500))

        buf.write(
            f"{current.isoformat()}\t"
            f"{server_time.isoformat()}\t"
            f"{DEVICE_ID}\t"
            f"rainfall\t"
            f"{round(counter, 2)}\n"
        )
        current += timedelta(minutes=5)

    buf.seek(0)
    return buf


class Command(BaseCommand):
    help = "Seed 1 year of mock telemetry data for device 26-6C-0E-F4-F9-23 (Batch COPY - fastest)"

    def handle(self, *args, **options):
        end = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
        start = end - timedelta(days=60)

        self.stdout.write(self.style.NOTICE(
            f"Seeding telemetry for device={DEVICE_ID}\n"
            f"  Range : {start.date()} → {end.date()}\n"
            f"  Method: Batch per sensor (safe & fast)\n"
            f"  Generating sensor data..."
        ))

        import time
        total_start = time.time()
        total_rows = 0

        with connection.cursor() as cursor:
            # Generate and insert regular sensors (one at a time)
            for sensor_key, interval_sec, base, amp, min_val, max_val in REGULAR_SENSORS:
                self.stdout.write(f"  ▸ {sensor_key}...", ending=" ")
                
                gen_start = time.time()
                buf = _generate_sensor_tsv(sensor_key, interval_sec, base, amp, min_val, max_val, start, end)
                gen_time = time.time() - gen_start
                
                row_count = buf.getvalue().count("\n")
                total_rows += row_count
                buf.seek(0)

                copy_start = time.time()
                cursor.copy_expert(COPY_SQL, buf)
                copy_time = time.time() - copy_start
                
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {row_count:,} rows ({gen_time:.1f}s gen + {copy_time:.1f}s copy)")
                )
            
            # Generate and insert rainfall
            self.stdout.write(f"  ▸ rainfall...", ending=" ")
            
            gen_start = time.time()
            buf = _generate_rainfall_tsv(start, end)
            gen_time = time.time() - gen_start
            
            row_count = buf.getvalue().count("\n")
            total_rows += row_count
            buf.seek(0)

            copy_start = time.time()
            cursor.copy_expert(COPY_SQL, buf)
            copy_time = time.time() - copy_start
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ {row_count:,} rows ({gen_time:.1f}s gen + {copy_time:.1f}s copy)")
            )
        
        total_time = time.time() - total_start
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Telemetry seed complete! Total rows: {total_rows:,} | Time: {total_time:.1f}s"
        ))

