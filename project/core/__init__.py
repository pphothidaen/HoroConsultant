"""
Computational Metaphysics Engine – Core Package
"""
try:
    from project.core.solar_time import calculate_true_solar_time, SolarTimeResult
except ImportError:
    calculate_true_solar_time = None
    SolarTimeResult = None

try:
    from project.core.bazi_engine import BaZiEngine
except ImportError:
    BaZiEngine = None

__all__ = ["calculate_true_solar_time", "SolarTimeResult", "BaZiEngine"]
