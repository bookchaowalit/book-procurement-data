---
title: Book Procurement Data — Product Card
doc_id: CARD-book-procurement-data
doc_type: product-card
verdict: showcase
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# Book Procurement Data — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ช่วยผู้ขายรายเล็กหรือทีมเล็กค้นหาประกาศจัดซื้อจัดจ้าง/ประมูลที่ยังเปิดอยู่ พร้อมประเภท (RFP/RFQ/tender) และเงื่อนไขผู้ขาย ในรูปแบบ contract `procurement.v1` ที่ตรวจสอบได้

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ประกาศจัดซื้อกระจายอยู่หลายแหล่งและอ่านยาก ผู้ขายรายเล็กพลาดกำหนดปิดรับได้ง่าย
- ผู้ใช้เป้าหมายตาม README: บุคคลและทีมเล็กที่หางาน procurement/tender (B2B/B2G) **[สมมติฐาน]** ยังไม่มีหลักฐานผู้ใช้จริง

## 3. สิ่งที่ทำได้จริงตอนนี้

- CLI `book-procurement-data` มีคำสั่ง `contract`, `demo` (ค้นหา/กรอง `--open-only`) และ `validate` สำหรับ export ที่ระบุชัด
- `capture.py` ดึงประกาศที่เปิดอยู่จาก Contracts Finder (OCDS search API ของสหราชอาณาจักร) ผ่าน shared lake runtime แบบสั่งด้วยมือ และจัดประเภท RFP/RFQ/vendor-registration/framework-agreement ด้วย regex แบบ deterministic
- ตัดอีเมล เบอร์โทร และ URL ออกจากข้อความคุณสมบัติก่อนออกผล; ไม่ fallback จาก live ไป fixture
- test 4 ไฟล์ทำงาน offline (contract, policy, shared CLI, source adapter)

## 4. หลักฐานสถานะ

- Stack: Python
- Commits: 11 (แรก 2026-09-09 → ล่าสุด 2026-10-01), branch `main`; working tree สะอาด
- Source: 8 ไฟล์ / 989 บรรทัด; test 4 ไฟล์
- CI: 1 workflow
- Deploy config: ไม่มี
- Live URL: ไม่พบใน repo
- โครงสร้างไฟล์เหมือนกับ repo อื่นอีก 12 ตัวในตระกูลเดียวกัน (structure signature เดียวกัน)
- แหล่งทางการที่เปิดใช้: 1 แหล่ง (`source-contracts-finder-open-tenders.json`)

## 5. คุณค่าและจุดต่าง

- จุดเด่นคือวินัยข้อมูล: แยก unknown ออกจาก false, ห้ามรวมมูลค่าคนละชนิด, มี lineage ก่อนติดป้าย `live`
- คู่แข่งคือพอร์ทัลจัดซื้อภาครัฐและบริการแจ้งเตือน tender ที่มีอยู่แล้ว; repo นี้ครอบคลุมแหล่งเดียวจึงยังไม่มีจุดต่างเชิงตลาด
- มุมรายได้: บริการแจ้งเตือน tender สำหรับ SME ไทย **[สมมติฐาน]** ต้องเพิ่มแหล่งไทย (เช่นระบบ e-GP) ก่อน **[ต้องยืนยัน]**

## 6. ช่องว่างสำคัญ

- มีแหล่งข้อมูลจริงเพียงแหล่งเดียว และเป็นแหล่งต่างประเทศ
- ยังไม่มีผู้ใช้ปลายทาง: README ระบุว่าไม่มี scheduler, hosted API หรือ consumer integration (`Consumers: integration planned`)
- เป็นหนึ่งใน 13 repo ที่ใช้โครงเดียวกัน แต่ละตัวบางมาก ทำให้ต้นทุนดูแล CI/README ซ้ำ 13 เท่า

## 7. คำตัดสิน

**showcase** — โค้ดทำงานจริงและเป็นหลักฐานงาน data engineering ที่ดี (contract, policy test, PII redaction) แต่ยังไม่มีผู้ใช้และครอบคลุมแหล่งเดียว จึงยังไม่ใช่ธุรกิจ

จะเปลี่ยนเป็น `invest` เมื่อมีแหล่งจัดซื้อของไทยอย่างน้อย 1 แหล่งและมี consumer จริง (เช่น digest รายสัปดาห์ที่มีคนใช้); ถ้าตระกูล 13 repo ถูกรวมเป็นแพ็กเกจเดียว ให้เปลี่ยนเป็น `merge` และชี้ไปที่แพ็กเกจนั้น

## 8. ขั้นต่อไป

1. ตัดสินใจระดับตระกูล: รวม 13 repo `book-*-data` (intake) เป็น multi-domain package เดียวหรือไม่
2. ประเมินความเป็นไปได้ของแหล่งจัดซื้อไทยและเงื่อนไขการใช้ข้อมูล
3. ต่อเข้ากับ consumer หนึ่งตัว (เช่น `book-opportunity-intelligence`) เพื่อพิสูจน์การใช้งาน

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `src/book_procurement_data/capture.py`
- `src/book_procurement_data/`
- `tests/`
