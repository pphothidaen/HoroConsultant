"""
Computational Metaphysics Engine – Core Package
"""
try:
    from project.core.solar_time import SolarTimeResult, calculate_true_solar_time
except ImportError:
    calculate_true_solar_time = None
    SolarTimeResult = None

try:
    from project.core.bazi_engine import BaZiEngine
except ImportError:
    BaZiEngine = None

__all__ = ["BaZiEngine", "SolarTimeResult", "calculate_true_solar_time"]
