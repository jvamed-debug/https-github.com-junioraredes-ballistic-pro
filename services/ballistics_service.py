import json
import os

class BallisticsService:
    _data = None

    @classmethod
    def load_data(cls):
        if cls._data is None:
            path = "database.json"
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    cls._data = json.load(f)
            else:
                cls._data = {"calibers": {}}
        return cls._data

    @classmethod
    def get_calibers(cls):
        data = cls.load_data()
        return list(data["calibers"].keys())

    @classmethod
    def get_caliber_details(cls, caliber):
        data = cls.load_data()
        return data["calibers"].get(caliber, {})

    @staticmethod
    def calculate_predicted_load(v_current, charge_current, v_target):
        """
        Simple linear prediction for load estimation (Use with caution!)
        """
        if v_current == 0: return 0
        return (v_target * charge_current) / v_current
