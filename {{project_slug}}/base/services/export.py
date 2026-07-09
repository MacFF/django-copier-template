from collections import OrderedDict


class ExportService:
    @classmethod
    def rename_column_from_dict(cls, data: dict, rename_mapping: dict):
        new_data = OrderedDict()  # handle key order change
        for key, value in data.items():
            new_key = rename_mapping.get(key, key)
            new_data[new_key] = value
        return new_data
