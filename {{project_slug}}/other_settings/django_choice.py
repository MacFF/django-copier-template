DRC_MODEL_CHOICES_SETTING = {
    # "rice_product_type": {
    #     "app": "general",
    #     "model": "RiceProductType",
    # },
    "user_permission": {
        "choice_class": "apis.authentication.choices.UserPermission"
    },
    "device": {
        "app": "device",
        "model": "Device",
    },
    "sensor": {
        "app": "device",
        "model": "Sensor",
        "controller": "apis.device.choices.SensorChoiceController",
    }
}
