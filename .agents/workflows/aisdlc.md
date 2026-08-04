# AI SDLC Workflow
1. **Plan**: Orchestrator วิเคราะห์ User Requirement และสร้างไฟล์ `plan.md`
2. **Code**: Orchestrator สั่ง `Developer` ให้ implement โค้ดตาม `plan.md` (รันคู่ขนานได้ถ้างานไม่ทับซ้อน)
3. **Test**: เมื่อโค้ดเสร็จ สั่ง `QA_Tester` ให้รัน Unit Test และ Integration Test
4. **Fix**: หาก Test ไม่ผ่าน ส่งผลลัพธ์กลับไปให้ `Developer` แก้ไข (Loop)
5. **Report**: Orchestrator สรุปผลลัพธ์และตำแหน่งไฟล์ส่งให้ User
