"""
project/core/base_engine.py — Standardized Base Engine Protocol & Data Models
Computational Metaphysics Engine
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ElementScores(BaseModel):
    """Five Elements (五行) percentage distribution."""
    wood: float = Field(0.0, description="Wood (木) percentage")
    fire: float = Field(0.0, description="Fire (火) percentage")
    earth: float = Field(0.0, description="Earth (土) percentage")
    metal: float = Field(0.0, description="Metal (金) percentage")
    water: float = Field(0.0, description="Water (水) percentage")

    def to_dict(self) -> Dict[str, float]:
        return self.model_dump()


class PillarData(BaseModel):
    """Pillar Stem-Branch pair."""
    stem: str = Field(..., description="Heavenly Stem (天干)")
    branch: str = Field(..., description="Earthly Branch (地支)")
    element: Optional[str] = Field(None, description="Primary Five Element")
    hidden_stems: Optional[List[str]] = Field(default_factory=list, description="Hidden Stems (藏干)")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class EngineChartResult(dict):
    """
    Standardized result payload for all metaphysical engines.
    Inherits directly from `dict` for 100% native compatibility with:
      • json.dumps(result)
      • isinstance(result, dict)
      • result["key"] dictionary indexing
      • result.engine_name attribute access
    """

    def __init__(
        self,
        engine_name: str,
        system_type: str,
        chart_data: Dict[str, Any],
        element_scores: Optional[Union[Dict[str, float], ElementScores]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        calculation_timestamp: Optional[str] = None,
    ):
        ts = calculation_timestamp or datetime.now(timezone.utc).isoformat()
        
        scores_dict = (
            element_scores.to_dict()
            if isinstance(element_scores, ElementScores)
            else element_scores
        )
        
        full_data = {
            **chart_data,
            "engine_name": engine_name,
            "system_type": system_type,
            "calculation_timestamp": ts,
        }
        if scores_dict is not None:
            full_data["element_scores"] = scores_dict
        if metadata:
            full_data["metadata"] = metadata

        super().__init__(full_data)
        
        self.engine_name = engine_name
        self.system_type = system_type
        self.calculation_timestamp = ts
        self.chart_data = chart_data
        self.element_scores = scores_dict
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Export clean standard dictionary."""
        return dict(self)


class AbstractAstrologyEngine(ABC):
    """
    Abstract Base Class for all 10 core calculation engines.
    Enforces standardized execution interface across domains.
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return human-readable engine name."""
        pass

    @property
    @abstractmethod
    def system_type(self) -> str:
        """Return system domain type identifier."""
        pass

    @abstractmethod
    def calculate(self, *args: Any, **kwargs: Any) -> EngineChartResult:
        """
        Execute core chart calculation logic.
        Must return a standardized EngineChartResult.
        """
        pass
