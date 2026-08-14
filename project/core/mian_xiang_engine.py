"""
Mian Xiang (麻衣神相) Facial Physiognomy Core Engine
=====================================================
Deterministic calculations for classical Chinese physiognomy rules:
- 12 Face Palaces (十二宮)
- 5 Facial Features (五官)
- Face Shape Classification (五行面相)
- Age-Period Fortune Flow (流年)
"""

from typing import Any
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

FACE_ELEMENTS = {
    "round": "Water (水形) - Round, soft, fleshy",
    "oval": "Metal (金形) - Oval, angular, defined",
    "square": "Earth (土形) - Square, thick, stable",
    "long": "Wood (木形) - Long, thin, rectangular",
    "pointed": "Fire (火形) - Pointed chin, wide forehead"
}

class MianXiangEngine(AbstractAstrologyEngine):
    """Core Mian Xiang (Facial Physiognomy) calculation engine."""

    @property
    def engine_name(self) -> str:
        return "Mian Xiang Physiognomy Engine"

    @property
    def system_type(self) -> str:
        return "mian_xiang"

    def analyze_face_shape(self, shape: str) -> str:
        """Classify face shape into Five Elements (五行面相)."""
        return FACE_ELEMENTS.get(shape.lower(), "Unknown")

    def analyze_12_palaces(self, features: dict[str, Any]) -> dict[str, str]:
        """Analyze the 12 Face Palaces (十二宮) based on facial features."""
        palaces = {}
        
        # 命宮 (Life Palace) - between eyebrows
        forehead = features.get("forehead", "")
        if forehead == "wide":
            palaces["命宮 (Life Palace)"] = "Broad and open, indicates good early fortune and open-mindedness."
        elif forehead == "narrow":
            palaces["命宮 (Life Palace)"] = "Narrow or obstructed, suggests early struggles or overthinking."
        else:
            palaces["命宮 (Life Palace)"] = "Average width, balanced early fortune."
            
        # 財帛宮 (Wealth Palace) - nose
        nose = features.get("nose", "")
        if nose == "high":
            palaces["財帛宮 (Wealth Palace)"] = "High nose bridge indicates strong wealth accumulation and ambition."
        elif nose == "wide":
            palaces["財帛宮 (Wealth Palace)"] = "Wide nose indicates good wealth capacity but possible leakage if nostrils are exposed."
        else:
            palaces["財帛宮 (Wealth Palace)"] = "Flat or other shape indicates variable wealth luck."

        # Other palaces (deterministic mappings for rule-based analysis)
        eyebrows = features.get('eyebrows', 'average')
        chin = features.get('chin', 'average')
        
        palaces["兄弟宮 (Siblings Palace)"] = f"Based on eyebrows: {eyebrows}"
        palaces["夫妻宮 (Spouse Palace)"] = "Outer eye area indicates marriage luck."
        palaces["子女宮 (Children Palace)"] = "Under-eye area (臥蠶) reflects descendants."
        palaces["疾厄宮 (Health Palace)"] = "Bridge of nose indicates physical constitution."
        palaces["遷移宮 (Travel Palace)"] = "Forehead sides reflect travel and migration fortune."
        palaces["奴僕宮 (Servants Palace)"] = f"Lower jaw: {chin}"
        palaces["官祿宮 (Career Palace)"] = f"Forehead center: {forehead}"
        palaces["田宅宮 (Property Palace)"] = "Upper eyelid area reflects real estate."
        palaces["福德宮 (Fortune Palace)"] = "Eyebrow tail area indicates mental state."
        palaces["父母宮 (Parents Palace)"] = "Forehead above eyebrows indicates parents' state."
        
        return palaces

    def analyze_5_officials(self, features: dict[str, Any]) -> dict[str, str]:
        """Analyze the 5 Facial Features (五官)."""
        officials = {}
        officials["採聽官 (Ears)"] = f"Ears are {features.get('ears', 'average')}. " + ("Good for listening and early years." if features.get("ears") == "large" else "Normal listening capacity.")
        officials["保壽官 (Eyebrows)"] = f"Eyebrows are {features.get('eyebrows', 'average')}. " + ("Strong longevity and sibling luck." if features.get("eyebrows") == "thick" else "Average longevity luck.")
        officials["監察官 (Eyes)"] = f"Eyes are {features.get('eyes', 'average')}. " + ("Good observation and spirit." if features.get("eyes") == "large" else "Focused spirit.")
        officials["審辨官 (Nose)"] = f"Nose is {features.get('nose', 'average')}. " + ("Good discernment and wealth." if features.get("nose") == "high" else "Standard discernment.")
        officials["出納官 (Mouth)"] = f"Mouth is {features.get('mouth', 'average')}. " + ("Good expression and intake." if features.get("mouth") == "full" else "Standard expression.")
        return officials

    def get_fortune_flow(self, birth_year: int) -> dict[str, str]:
        """Map ages to facial regions (流年)."""
        return {
            "1-14": "Ears (Ears govern early childhood)",
            "15-30": "Forehead (Youth and early career)",
            "31-34": "Eyebrows (Early 30s development)",
            "35-40": "Eyes (Mid-30s transition)",
            "41-50": "Nose (Peak wealth and mid-life)",
            "51-60": "Mouth/Upper Lip (Late career)",
            "61-75": "Lower Face/Jaw (Retirement)",
            "76+": "Chin/Jawline (Late life)"
        }

    def analyze(self, features_dict: dict[str, Any], birth_year: int | None = None) -> EngineChartResult:
        """Main analysis entrypoint for Mian Xiang rules."""
        face_shape = features_dict.get("face_shape", "")
        face_element = self.analyze_face_shape(face_shape)
        twelve_palaces = self.analyze_12_palaces(features_dict)
        five_officials = self.analyze_5_officials(features_dict)
        
        # Moles
        moles_analysis = []
        for mole in features_dict.get("moles", []):
            loc = mole.get("location", "unknown")
            size = mole.get("size", "small")
            moles_analysis.append(f"Mole at {loc} ({size}) - Requires specific location mapping for full meaning.")
            
        fortune_flow = self.get_fortune_flow(birth_year) if birth_year else None
        
        overall = f"Face belongs to {face_element}. The 5 officials and 12 palaces present a complete physiognomy profile."

        chart_data = {
            "face_element": face_element,
            "twelve_palaces": twelve_palaces,
            "five_officials": five_officials,
            "moles": moles_analysis,
            "overall_assessment": overall
        }
        if fortune_flow:
            chart_data["fortune_flow"] = fortune_flow
            
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=chart_data
        )

    def calculate(self, *args: Any, **kwargs: Any) -> EngineChartResult:
        """Standardized interface for base engine."""
        if args and isinstance(args[0], dict):
            return self.analyze(args[0], kwargs.get("birth_year"))
        return self.analyze(kwargs.get("features_dict", {}), kwargs.get("birth_year"))

if __name__ == "__main__":
    mx = MianXiangEngine()
    features = {
        "face_shape": "round",
        "forehead": "wide",
        "eyebrows": "thick",
        "eyes": "large",
        "nose": "high",
        "mouth": "full",
        "ears": "large",
        "chin": "round",
        "moles": [{"location": "left cheek", "size": "small"}]
    }
    print(mx.calculate(features, birth_year=1990))
