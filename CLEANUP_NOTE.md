# Cleanup Note — Logging files (pending archive)

- วันที่: 2026-10-17
- เป้าหมาย: ระบุไฟล์ log ที่เหลือไม่ได้ clean เนื่องจาก tracked
- สถานะ: ควร clean ในภายหลัง (if not used)

## ไฟล์ที่เก็บไว้ (tracked, ไม่ลบ)

| ไฟล์ | ขนาด | ต้นเหตุ | action |
|-------|-------|---------|--------|
| `project/kaggle_kernel/horoconsultant-finetune-pipeline.log` | 38 KB | tracked ใน git | ควร clean ในภายหลัง (if not used) |
| `project/kaggle_kernel/train_execution.log` | 9 KB | tracked ใน git | ควร clean ในภายหลัง (if not used) |

## ตัดสินใจ

- ไม่ลบ (git-tracked) ✅
- เพิ่ม `.gitignore` ครอบคลุม ✅
- เอกสารหมายเหตุ (นี้) ✅
- ต้องการ clean ในภายหลัง: จัดการ archive / unstage ครับ

## ตรวจสอบ

- git status: ไฟล์ 2 ไฟล์นี้ยัง tracked (ไม่ลบได้ครับ)
- เวลาจะ clean ในภายหลัง: git rm + commit หรือ git rm --cached + commit
