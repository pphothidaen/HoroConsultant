# Kaggle Hybrid Strategy Tradeoff Matrix

ใช้เมื่อคุณต้องตัดสินใจเรื่องสถาปัตยกรรมระหว่าง
- **Option A:** ทำ Kaggle เป็นเส้นทาง Production Path
- **Option B:** รักษา Kaggle ไว้เฉพาะงานวิจัย/รีเทรน และรัน Production ตาม infra หลัก

| เกณฑ์ | Option A: Kaggle in Prod Path | Option B: Hybrid (ขณะนี้) |
|---|---|---|
| ความเสถียรของ Production (0-5) | 2 | 5 |
| การควบคุมต้นทุน (0-5) | 2 | 5 |
| ความสามารถขยายระบบ (0-5) | 2 | 5 |
| ความเสี่ยงด้านความล่าช้า/timeout (0-5) | 2 | 4 |
| ความเหมาะสมกับการ E2E ต่อเนื่อง (0-5) | 3 | 5 |
| ความซับซ้อนในการผสาน CI/CD (0-5) | 2 | 4 |
| **รวมคะแนน** | **16/30** | **28/30** |

### สรุปสั้น
- ถ้าต้องการระบบ production ที่เสถียรและคุมต้นทุน: เลือก **Hybrid**
- ถ้าต้องการ Kaggle ใช้งานเท่านั้น: จำกัดเฉพาะ training workflow ที่ explicit เท่านั้น

### การแมปไปยังงานที่ทำใน repo
- `scripts/run_prod_e2e_playwright.py`
  - มี `--profile smoke|full`
  - `smoke` = ชุดตรวจหลักเร็วและคุ้มค่า
  - `full` = ตรวจเต็มทุก Discipline (ใช้เฉพาะ manual)
- `.github/workflows/ai_cicd.yml`
  - `kaggle-ai-cicd` รันเฉพาะ `workflow_dispatch` + `run_kaggle_cloud=true`
  - เพิ่มขั้น `run_prod_e2e_playwright.py --profile` แบบ manual สำหรับเลือก `smoke/full`

### ปรับการใช้จริงแบบสั้น
```bash
# Smoke by default
python3 scripts/run_prod_e2e_playwright.py

# Full profile (เมื่อจำเป็น)
python3 scripts/run_prod_e2e_playwright.py --profile full

# Manual Workflow dispatch examples (GitHub)
# run_kaggle_cloud: false (default)
# e2e_profile: smoke | full
```

`run_kaggle_cloud` ต้องเปิดเฉพาะกรณีต้อง trigger/re-sync Kaggle pipeline เท่านั้น
