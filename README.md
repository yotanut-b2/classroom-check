# ระบบสังเกตชั้นเรียนบนอาคารเรียน

เว็บแอพ Streamlit สำหรับบันทึกผลการสังเกตชั้นเรียนตามอาคาร/ชั้น พร้อม Dashboard, จัดการข้อมูล, ดาวน์โหลด Excel และพิมพ์รายงาน PDF

## วิธีติดตั้ง

เปิด Command Prompt หรือ PowerShell ที่โฟลเดอร์นี้ แล้วรัน:

```powershell
python -m pip install -r requirements.txt
```

## วิธีเปิดระบบ

```powershell
streamlit run app.py
```

## การเข้าสู่ระบบ

- Admin: username `admin`, password `654321`
- ผู้ตรวจอาคาร: username เป็นชื่อในไฟล์ `data/examiner_ssm.xlsx`, password `123456`

ผู้ตรวจทั่วไปจะเข้าได้เฉพาะวันที่มีชื่ออยู่ในคอลัมน์วันนั้น เช่น Monday, Tuesday, Wednesday, Thursday, Friday

## ไฟล์ข้อมูล

- `data/examiner_ssm.xlsx` ตารางเวรตรวจอาคาร
- `data/criteria_classroom.xlsx` เกณฑ์การประเมิน
- `data/teacher_list.xlsx` รายชื่อครูผู้สอน
- `data/data_classroom_log.csv` ไฟล์บันทึกสำรองในเครื่อง ระบบจะสร้างให้อัตโนมัติเมื่อมีการใช้งาน

## หมายเหตุ

รุ่นนี้ตั้งค่าให้ส่งข้อมูลไป Google Sheet ผ่าน Apps Script แล้ว โดยอ่านค่าจาก `.streamlit/secrets.toml`

```toml
[apps_script]
url = "Web app URL ที่ลงท้ายด้วย /exec"
token = "รหัสเดียวกับ TOKEN ใน Apps Script"
```

ระบบจะบันทึก CSV ในเครื่องควบคู่ไปด้วยเสมอ เพื่อใช้เป็นข้อมูลสำรองหากอินเทอร์เน็ตหรือ Apps Script ใช้งานไม่ได้
