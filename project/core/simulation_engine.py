"""
project/core/simulation_engine.py
=================================
Life Path Multi-Scenario Simulation & What-If Analyzer Engine.
Simulates multi-year career, business, and relocation trajectories based on transit math.
"""

from typing import Any, Dict, List, Optional
import datetime

# Predefined Life Scenarios
PRESET_SCENARIOS = [
    {
        "id": "corporate_stay",
        "title": "ทำงานประจำต่อ / เติบโตตามสายงานองค์กร (Stay at Corporate Job)",
        "elements": ["Earth", "Metal"],
        "base_wealth": 65,
        "base_career": 70,
        "base_stability": 85,
        "base_innovation": 40,
        "risk_tier": "LOW",
        "icon": "🏢"
    },
    {
        "id": "tech_startup",
        "title": "ย้ายไปร่วมงาน Tech Startup ดาวรุ่ง (Pivot to High-Growth Startup)",
        "elements": ["Fire", "Wood"],
        "base_wealth": 80,
        "base_career": 85,
        "base_stability": 55,
        "base_innovation": 90,
        "risk_tier": "MEDIUM_HIGH",
        "icon": "🚀"
    },
    {
        "id": "business_startup",
        "title": "ลาออกมาเปิดธุรกิจส่วนตัว / E-Commerce (Launch Own Venture)",
        "elements": ["Fire", "Water"],
        "base_wealth": 90,
        "base_career": 90,
        "base_stability": 45,
        "base_innovation": 85,
        "risk_tier": "HIGH",
        "icon": "💼"
    },
    {
        "id": "overseas_relocation",
        "title": "ย้ายไปทำงาน / ขยายธุรกิจต่างประเทศ (Relocate & Expand Overseas)",
        "elements": ["Water", "Wood"],
        "base_wealth": 85,
        "base_career": 80,
        "base_stability": 60,
        "base_innovation": 80,
        "risk_tier": "MEDIUM",
        "icon": "🌏"
    }
]

# Annual Transit Pillars & Element Weights (2026 - 2030)
TRANSIT_YEARS = {
    2026: {"pillar": "丙午 (Bing-Wu)", "dominant_elements": ["Fire"]},
    2027: {"pillar": "丁未 (Ding-Wei)", "dominant_elements": ["Fire", "Earth"]},
    2028: {"pillar": "戊申 (Wu-Shen)", "dominant_elements": ["Earth", "Metal"]},
    2029: {"pillar": "己酉 (Ji-You)", "dominant_elements": ["Earth", "Metal"]},
    2030: {"pillar": "庚戌 (Geng-Xu)", "dominant_elements": ["Metal", "Earth"]}
}


class SimulationEngine:
    """Computes comparative multi-year life decision scenario trajectories."""

    @staticmethod
    def get_presets() -> List[Dict[str, Any]]:
        return PRESET_SCENARIOS

    @staticmethod
    def simulate_scenarios(
        birth_datetime: str,
        scenario_ids: Optional[List[str]] = None,
        custom_scenarios: Optional[List[Dict[str, Any]]] = None,
        start_year: int = 2026,
        horizon_years: int = 3,
        day_master: Optional[str] = "甲 (Jia Wood)"
    ) -> Dict[str, Any]:
        """Run multi-scenario simulation across timeline horizon."""
        active_scenarios = []

        if scenario_ids:
            preset_map = {s["id"]: s for s in PRESET_SCENARIOS}
            for sid in scenario_ids:
                if sid in preset_map:
                    active_scenarios.append(preset_map[sid])

        if custom_scenarios:
            for cs in custom_scenarios:
                active_scenarios.append({
                    "id": cs.get("id", f"custom_{len(active_scenarios)+1}"),
                    "title": cs.get("title", "แผนทางเลือกเฉพาะบุคคล"),
                    "elements": cs.get("elements", ["Fire", "Earth"]),
                    "base_wealth": cs.get("base_wealth", 75),
                    "base_career": cs.get("base_career", 75),
                    "base_stability": cs.get("base_stability", 65),
                    "base_innovation": cs.get("base_innovation", 70),
                    "risk_tier": cs.get("risk_tier", "MEDIUM"),
                    "icon": "✨"
                })

        if not active_scenarios:
            active_scenarios = PRESET_SCENARIOS[:3]

        end_year = min(start_year + horizon_years, 2031)
        years = list(range(start_year, end_year))

        simulated_results = []

        for scen in active_scenarios:
            yearly_metrics = []
            total_composite = 0.0

            for y in years:
                transit_info = TRANSIT_YEARS.get(y, {"pillar": "Transit Year", "dominant_elements": ["Earth"]})
                dom_elements = transit_info["dominant_elements"]

                # Check elemental resonance (+10 if scenario matches transit element)
                match_count = sum(1 for e in scen["elements"] if e in dom_elements)
                boost = match_count * 8

                wealth = min(100, max(20, scen["base_wealth"] + boost + ((y - 2026) * 3)))
                career = min(100, max(20, scen["base_career"] + boost + ((y - 2026) * 2)))
                stability = min(100, max(20, scen["base_stability"] - (boost // 2) + ((y - 2026) * 1)))
                innovation = min(100, max(20, scen["base_innovation"] + boost))

                composite = round((wealth * 0.35 + career * 0.30 + stability * 0.20 + innovation * 0.15), 1)
                total_composite += composite

                yearly_metrics.append({
                    "year": y,
                    "pillar": transit_info["pillar"],
                    "wealth_score": wealth,
                    "career_score": career,
                    "stability_score": stability,
                    "innovation_score": innovation,
                    "composite_score": composite
                })

            avg_score = round(total_composite / len(years), 1)

            # Strategy formulation
            if scen["risk_tier"] == "LOW":
                strategy = "เส้นทางปลอดภัย เหมาะสำหรับเน้นเสถียรภาพและสะสมประสบการณ์ระยะยาว"
            elif scen["risk_tier"] in ("HIGH", "MEDIUM_HIGH"):
                strategy = f"เส้นทางเติบโตแบบก้าวกระโดด ปีทองแห่งผลตอบแทนคือ {years[0]} ด้วยพลังธาตุ {scen['elements'][0]}"
            else:
                strategy = "เส้นทางขยายขอบเขตและโอกาสใหม่ เหมาะแก่การสร้างคอนเนกชันสากล"

            simulated_results.append({
                "scenario_id": scen["id"],
                "title": scen["title"],
                "icon": scen["icon"],
                "risk_tier": scen["risk_tier"],
                "elements": scen["elements"],
                "composite_roi": avg_score,
                "yearly_metrics": yearly_metrics,
                "strategy_advice": strategy
            })

        # Sort descending by composite_roi
        simulated_results.sort(key=lambda x: x["composite_roi"], reverse=True)
        optimal = simulated_results[0]

        return {
            "birth_datetime": birth_datetime,
            "day_master": day_master,
            "horizon_years": horizon_years,
            "years_evaluated": years,
            "scenarios_count": len(simulated_results),
            "optimal_scenario_id": optimal["scenario_id"],
            "optimal_scenario_title": optimal["title"],
            "optimal_summary": f"เส้นทางที่ให้ผลลัพธ์คุ้มค่าสูงสุดคือ '{optimal['title']}' ด้วยคะแนนเฉลี่ย {optimal['composite_roi']} คะแนน",
            "results": simulated_results
        }


simulation_engine = SimulationEngine()
