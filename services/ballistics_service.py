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
        Cálculo de predição linear para estimativa de carga.
        
        ⚠️ AVISO DE SEGURANÇA (AUDITORIA FUN-001):
        Balística interna NÃO é linear. Este cálculo é uma estimativa matemática simplificada 
        e NÃO considera picos de pressão de câmara. O uso indevido pode causar falhas 
        catastróficas no equipamento e riscos à vida.
        Consulte sempre tabelas de recarga oficiais (SAAMI/CIP).
        """
        if v_current == 0:
            return 0
        return (v_target * charge_current) / v_current

    # Fatores de conversão exatos, isolados para que os testes possam fixá-los.
    GRAIN_TO_KG = 0.0000647989
    GRAM_TO_GRAIN = 15.4324
    FPS_TO_MS = 0.3048

    @classmethod
    def muzzle_energy_joules(cls, projectile_grains: float, velocity_fps: float) -> float:
        """Energia cinética na boca do cano, em joules."""
        mass_kg = projectile_grains * cls.GRAIN_TO_KG
        velocity_ms = velocity_fps * cls.FPS_TO_MS
        return 0.5 * mass_kg * velocity_ms ** 2

    @classmethod
    def estimate_charge_grains(
        cls,
        projectile_grains: float,
        velocity_fps: float,
        calorific_j_per_g: float,
        efficiency_percent: float,
    ) -> float:
        """Massa de pólvora que entregaria essa energia, pela conservação de energia.

        Modelo termodinâmico de primeira ordem: energia do projétil dividida
        pela energia útil por grama de pólvora. Ignora a curva de pressão, o
        volume da câmara e o tempo de queima, então serve para comparar
        ordens de grandeza — nunca para definir uma carga real.
        """
        if calorific_j_per_g <= 0 or efficiency_percent <= 0:
            return 0.0
        energy_j = cls.muzzle_energy_joules(projectile_grains, velocity_fps)
        powder_g = energy_j / (calorific_j_per_g * (efficiency_percent / 100))
        return powder_g * cls.GRAM_TO_GRAIN

