from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command

from apis.authentication.models import DeviceToken
from apis.device.models import SensorType, SensorUnit
from {{project_slug}}.base.models import get_system_user


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running sensor seed..."))
        self.create_sensor_unit()
        self.create_sensor_type()
        self.stdout.write(self.style.SUCCESS("sensor seeds done."))
    
    def create_sensor_unit(self):
        units = [
            "kWh", "Wh", "m³", "%", "Nm³", "Hz", "ppm", "Lux", "Bar", "V",
            "°", "mm", "°C", "F", "W", "mm/s", "m³/h", "m/s", "psi", "A",
            "dB", "m³/s", "µg/m³", "ppb", "m³/min", "µS/cm", "mg/l", "kW",
            "°C Td", "μS/m", "L", "mmHg", "degree", "degree/hr"
        ]

        for unit in units:
            SensorUnit.objects.get_or_create(symbol=unit, is_default=True)
    
    def create_sensor_type(self):
        sensor_type_names = [
            # Environmental
            ("อุณหภูมิ", "Temperature"),
            ("ความชื้นในดิน", "Soil Moisture"),
            ("อุณหภูมิในดิน", "Soil Temperature"),
            ("ความเอียงหน้าดิน", "Soil Tilt"),
            ("ความชื้น", "Humidity"),
            ("ปริมาณน้ำฝนสะสม", "Rainfall"),
            # ("ปริมาณน้ำฝน", "Rainfall"),
            # ("ความดัน", "Pressure"),
            # ("คาร์บอนไดออกไซด์", "CO2"),
            # ("คาร์บอนมอนอกไซด์", "CO"),
            # ("PM2.5, PM2.5"),
            # ("PM10", "PM10"),
            # ("VOC", "VOC"),
            # ("ระดับเสียง", "Noise"),
            # ("ความเข้มแสง", "Light"),
            # ("ดัชนี UV", "UV Index"),
            # ("ความเร็วลม", "Wind Speed"),
            # ("ทิศทางลม", "Wind Direction"),
            # # Water
            # ("ระดับน้ำ", "Water Level"),
            # ("อัตราการไหลของน้ำ", "Water Flow"),
            # ("อุณหภูมิน้ำ", "Water Temperature"),
            # ("pH", "pH"),
            # ("ความขุ่น", "Turbidity"),
            # ("ออกซิเจนละลายน้ำ", "Dissolved Oxygen"),
            # ("ค่าการนำไฟฟ้า", "Conductivity"),
            # # Electrical
            # ("แรงดันไฟฟ้า", "Voltage"),
            # ("กระแสไฟฟ้า", "Current"),
            # ("กำลังไฟฟ้า", "Power"),
            # ("พลังงานไฟฟ้า", "Energy"),
            # ("ความถี่", "Frequency"),
            # ("ตัวประกอบกำลัง", "Power Factor"),
            # # Motion / Position
            # ("การเคลื่อนไหว", "Motion"),
            # ("การสั่นสะเทือน", "Vibration"),
            # ("การเอียง", "Tilt"),
            # ("ระยะทาง", "Distance"),
            # ("ละติจูด GPS", "GPS Latitude"),
            # ("ลองจิจูด GPS", "GPS Longitude"),
            # # Tank / Industrial
            # ("ระดับเชื้อเพลิง", "Fuel Level"),
            # ("การรั่วของแก๊ส", "Gas Leak"),
            # ("ควัน", "Smoke"),
            # ("เปลวไฟ", "Flame"),
        ]

        for label, name in sensor_type_names:
            SensorType.objects.update_or_create(
                name=name, defaults={"label": label, "is_default": True}
            )
