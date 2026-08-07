---
name: bazi-calculator
description: Deterministic BaZi 4-Pillars, True Solar Time & Five Elements calculation skill
---

# ☯️ BaZi Calculator Skill

### Purpose
Computes Four Pillars of Destiny (四柱命理) chart for birth date/time and location with True Solar Time (TST) adjustment ($TST = LMT + EoT$).

### Input Format
```json
{
  "birth_datetime": "1990-05-15 14:30:00",
  "longitude": 100.4930,
  "utc_offset_hours": 7.0,
  "unknown_hour": false
}
```

### Usage
```python
from project.core.bazi_engine import BaZiEngine
chart = BaZiEngine().calculate("1990-05-15 14:30:00", 100.4930, 7.0)
```
