# 📘 دليل التوثيق البرمجي الشامل (Developer Documentation)
## موديول الامتثال ومكافحة غسل الأموال لمنصة تحصيل | `tahseel_aml`
**مرجع تقني متكامل لمطوري منصة تحصيل (Ultimate Pay Developers)**
**معتمد رسمياً ومطابق لمواصفات مزود نظام الامتثال ومكافحة غسل الأموال `Requirements_UP_F.pdf` (Kanji / EFRM Engine)**

---

## 📑 فهرس المحتويات
1. [نظرة عامة والهدف المعماري (Architecture Overview)](#1-نظرة-عامة-والهدف-المعماري)
2. [هيكلية التطبيق ومبدأ المسؤولية الأحادية (App Structure & SOLID)](#2-هيكلية-التطبيق-ومبدأ-المسؤولية-الأحادية)
3. [طبقة النماذج وقواعد البيانات (Models Layer)](#3-طبقة-النماذج-وقواعد-البيانات)
4. [طبقة العقود والواجهات المجردة (Interfaces Layer)](#4-طبقة-العقود-والواجهات-المجردة)
5. [محرك التحقق وقواعد العمل الرقابية (Validators Engine)](#5-محرك-التحقق-وقواعد-العمل-الرقابية)
6. [طبقة الخدمات ومحرك المخاطر (Services & Risk Engine)](#6-طبقة-الخدمات-ومحرك-المخاطر)
7. [مواصفات الربط مع محرك فحص العقوبات EFRM Screening (وثيقة المتطلبات الرسمية)](#7-مواصفات-الربط-مع-محرك-فحص-العقوبات-efrm-screening)
8. [مواصفات محرك مراقبة المعاملات المالية اللحظية (Transaction Monitoring - EFRM)](#8-مواصفات-محرك-مراقبة-المعاملات-المالية-اللحظية)
9. [معالجة إشعارات الـ Webhooks والقرارات غير المتزامنة (Webhooks & Callbacks)](#9-معالجة-إشعارات-الـ-webhooks-والقرارات-غير-المتزامنة)
10. [دليل بناء واجهات الـ API لمنصة تحصيل (DRF Integration Guide)](#10-دليل-بناء-واجهات-الـ-api-لمنصة-تحصيل)
11. [لوحة التحكم الرقابية (Django Admin)](#11-لوحة-التحكم-الرقابية)
12. [دليل النشر والترحيل على السيرفر (Deployment & Migrations)](#12-دليل-النشر-والترحيل-على-السيرفر)

---

## 1. نظرة عامة والهدف المعماري

تطبيق `tahseel_aml` هو تطبيق جانغو (Django App) مستقل ومُصمم للإضافة المباشرة داخل مشروع منصة **تحصيل (Ultimate Pay)**.

### الهدف الوظيفي:
* إدارة دورة حياة المفوترين (Billers) من المنظور الرقابي ومكافحة غسل الأموال (AML/CFT).
* إلزام المفوترين بتسجيل الأطراف المرتبطة (ملاك، شركاء، مفوضين، ومدراء تنفيذيين).
* احتساب **المستفيد الحقيقي (UBO)** تلقائياً لمن يملك حصة &ge; 25%.
* فحص وتتبع **الأشخاص المعرضين سياسياً (PEP)** ومتطلبات الامتثال الضريبي الأمريكي **(FATCA)**.
* **فحص العقوبات والقوائم المحظورة (Watchlist Screening)** للكيان التجاري (Primary Entity) وجميع الأطراف المرتبطة (Secondary Related Entities) بالربط المباشر مع محرك **Kanji EFRM**.
* **مراقبة المعاملات المالية (Transaction Monitoring - EFRM)** بنمطي الفحص المتزامن (SYNC) وغير المتزامن (ASYNC) عبر قنوات POS و ECOM و ATM.
* استقبال ومعالجة إشعارات **Webhooks** للقرارات غير المتزامنة وتحديثات القضايا الرقابية المغلقة (Case Action Updates).
* حفظ وتجميد سجلات الرقابة والتدقيق لمدة **10 سنوات** وفقاً لتعليمات البنك المركزي (CBY).

---

## 2. هيكلية التطبيق ومبدأ المسؤولية الأحادية

تم بناء التطبيق وفق معمارية الطبقات النظيفة (Clean Layered Architecture) ومبادئ SOLID:

```text
tahseel_aml/
├── __init__.py                 # حزمة بايثون
├── apps.py                     # إعدادات التطبيق (TahseelAmlConfig)
├── admin.py                    # لوحة الإدارة لضباط الامتثال مع أقفال الأمان
├── views.py                    # واجهات استقبال الـ Webhooks وفحص الصحة
├── urls.py                     # مسارات الربط الشبكي للتطبيق
├── DEVELOPER_DOCUMENTATION.md  # هذا الدليل التوثيقي الشامل
│
├── models/                     # [طبقة البيانات - Data Layer]
│   ├── __init__.py             # تصدير موحد لجميع النماذج والخيارات
│   ├── choices.py              # قوائم الخيارات الرقابية وخيارات EFRM (Enums)
│   ├── base.py                 # نماذج التجريد وحماية السجلات (Immutability)
│   ├── biller.py               # نموذج المفوتر ومؤشرات EFRM والصانع/المراجع
│   ├── party.py                # نموذج الأطراف والشركاء و UBO/PEP/FATCA والجنس
│   ├── document.py             # نموذج الوثائق والمستندات الثبوتية
│   ├── screening.py            # سجلات فحص العقوبات وسجلات التدقيق الرقابي
│   └── transaction.py          # سجلات مراقبة المعاملات المالية وأحداث Webhook
│
├── interfaces/                 # [طبقة العقود والواجهات - SOLID DIP]
│   └── __init__.py             # تعريف الواجهات المجردة (ABCs)
│
├── validators/                 # [طبقة محركات التحقق - Single Responsibility]
│   └── __init__.py             # مدققات الكيانات الأربعة والأطراف
│
└── services/                   # [طبقة الخدمات ومنطق الأعمال - Strategy Pattern]
    ├── __init__.py             # خدمة إدارة المفوتر، محرك المخاطر، وخدمة التدقيق
    ├── kanji_client.py         # عميل الربط المباشر مع محرك Kanji EFRM / AML
    └── webhook_service.py      # معالج إشعارات Webhook للقرارات وتحديثات القضايا
```

---

## 3. طبقة النماذج وقواعد البيانات (Models Layer)

جميع النماذج تستخدم معرّفات فريدة عالمية `UUID` لمنع التخمين الأمني (Insecure Direct Object References - IDOR).

### أ) النماذج المجردة (`models/base.py`)
1. **`TimeStampedUUIDModel`**:
   * يضيف `id = UUIDField(primary_key=True)` و `created_at` و `updated_at`.
2. **`ImmutableComplianceModel`**:
   * نموذج رقابي صارم. يمنع برمجياً استدعاء `.delete()` أو تعديل السجل بعد حفظه، للامتثال لمتطلبات البنك المركزي بحفظ السجلات دون أي إمكانية للتعديل أو الحذف.

### ب) نموذج المفوتر (`models/biller.py` -> `Biller`)
* **البيانات الأساسية:** `biller_code`, `biller_type`, `name_ar`, `name_en`, `sector`, `mcc_code`.
* **البيانات القانونية والضريبية:** `commercial_register_number`, `license_number`, `tax_number`, `country_code` (ISO Alpha-2), `entity_sub_type`.
* **مؤشرات EFRM المالية:**
  * `expected_monthly_volume`: سقف حجم المبيعات الشهري المتوقع.
  * `expected_monthly_count`: عدد العمليات الشهري المتوقع.
  * `expected_avg_amount`: متوسط قيمة الفاتورة.
  * `max_single_amount`: الحد الأقصى للعملية الواحدة.
* **ملف مخاطر الامتثال:** `risk_level` (LOW, MEDIUM, HIGH, PROHIBITED), `risk_score` (0-100), `requires_edd` (عناية واجبة معززة).
* **حوكمة الصانع والمراجع (Maker/Checker):**
  * `status`: DRAFT, PENDING_MAKER, PENDING_CHECKER, ACTIVE, SUSPENDED, FROZEN, REJECTED.
  * `maker_user`, `maker_submitted_at`.
  * `checker_user`, `checker_approved_at`, `checker_notes`.

### ج) نموذج الأطراف المرتبطة (`models/party.py` -> `BillerParty`)
* **الدور الرقابي:** `role` (OWNER, PARTNER, AUTHORIZED_SIGNATORY, BOARD_MEMBER, UBO).
* **الهوية:** `id_type`, `id_number`, `id_issue_date`, `id_expiry_date`, `date_of_birth`, `nationality`, `country_code` (ISO Alpha-2), `gender` (MALE, FEMALE).
* **الملكية:** `equity_percentage` (نسبة الحصة حتى منزلتين عشريتين).
* **احتساب المستفيد الحقيقي التلقائي (UBO):**
  * عند الحفظ (`save()`)، إذا كانت `equity_percentage >= 25.00`، يتم ضبط `is_ubo = True` تلقائياً.
* **الأشخاص المعرضون سياسياً (PEP):**
  * `is_pep`, `pep_position`, `pep_entity`, `pep_risk_severity`.
* **الامتثال الأمريكي (FATCA):**
  * `fatca_status`, `us_tax_id`.

### د) نموذج سجلات فحص العقوبات (`models/screening.py` -> `AMLScreeningRecord`)
* يحفظ استجابة محرك EFRM بدقة كاملة:
  * `client_request_id`: معرّف الطلب لدى تحصيل.
  * `provider_request_id`: معرّف الطلب لدى محرك EFRM.
  * `decision`: NO_MATCH, POTENTIAL_MATCH, CONFIRMED_MATCH, FALSE_POSITIVE.
  * `risk_band`: LOW, MEDIUM, HIGH, CRITICAL.
  * `overall_risk_score`: درجة الخطورة (0-1000).
  * `match_score`: نسبة التطابق (%).
  * `matched`: هل يوجد تطابق.
  * `hit_count`: عدد التطابقات في القوائم.
  * `matched_lists`: القوائم المتطابقة (OFAC, UN, CBY, ...).
  * `alert_generated`, `case_generated`, `case_id`, `recommended_action`, `screened_at`.
  * `raw_request_payload`, `raw_response_payload`.

### هـ) نموذج مراقبة العمليات المالية وأحداث الـ Webhooks (`models/transaction.py`)
1. **`AMLTransactionMonitoringRecord`**:
   * يحفظ فحص الحركات المالية (POS, ECOM, ATM) عبر بطاقات الدفع أو المحافظ.
   * `source_txn_id`, `pan_masked`, `amount`, `currency_code`, `decision`, `risk_score`, `risk_severity`, `policy_code`, `signals`.
2. **`AMLWebhookEvent`**:
   * يسجل كل حدث Webhook وارد من EFRM (للتحقق من استلام الأحداث وعدم تكرارها Idempotency).

---

## 4. طبقة العقود والواجهات المجردة (Interfaces Layer)

مبنية وفق مبدأ انعكاس التبعية (Dependency Inversion Principle - DIP):

1. **`IBillerValidator`**: واجهة للتحقق من هيكل المنشأة وتوافق أطرافها.
2. **`IPartyValidator`**: واجهة للتحقق من بيانات الطرف المرتبط (العمر، الهوية، PEP، FATCA).
3. **`IRiskCalculationStrategy`**: واجهة خوارزمية احتساب درجة المخاطر.
4. **`ISanctionsScreeningClient`**: واجهة عميل فحص العقوبات (فحص المنشآت وفحص الأفراد).
5. **`ITransactionMonitoringClient`**: واجهة عميل تقييم مخاطر المعاملات المالية اللحظية.
6. **`IAuditLogger`**: واجهة توثيق العمليات في سجل التدقيق الرقابي غير القابل للتعديل.

---

## 5. محرك التحقق وقواعد العمل الرقابية (Validators Engine)

تطبيق مبدأ المسؤولية الأحادية (SRP) ومبدأ المفتوح/المغلق (OCP):
* **`GovernmentBillerValidator`**: يتحقق من وجوب وجود مفوض بالتوقيع رسمي واحد على الأقل مع منع تسجيل ملاك أو شركاء للجهات الحكومية.
* **`MerchantBillerValidator`**: يتحقق من وجود مالك واحد بنسبة 100% ورقم سجل تجاري وهوية سارية.
* **`PrivateCompanyBillerValidator`**: يتحقق من أن مجموع حصص الشركاء = 100.00% بالضبط (باستخدام `aggregate(Sum())` على مستوى قاعدة البيانات)، وجود شريكين على الأقل، مفوض بالتوقيع، ومستفيد حقيقي (UBO) واحد على الأقل.
* **`MixedCompanyBillerValidator`**: يتحقق من أن مجموع الحصص = 100.00% ووجود مفوض بالتوقيع.
* **`PartyComplianceValidator`**: يتحقق من أن عمر الشخص لا يقل عن 18 عاماً، سريان الهوية، والتحقق الإلزامي من بيانات المنصب لـ PEP وبيانات الضرائب لـ FATCA.

---

## 6. طبقة الخدمات ومحرك المخاطر (Services & Risk Engine)

* **`StandardRiskCalculationStrategy`**: احتساب المخاطر استناداً لقطاع النشاط (الجمعيات الخيرية والمؤسسات المالية ترفع النقاط)، وجود PEP، ونتائج الفحص الرقابي.
* **`BillerComplianceService`**: الخدمة المركزية المنسقة لعمليات التحقق، احتساب المخاطر، وفحص العقوبات الشامل للكيان وأطرافه.
* **`AuditService`**: تسجيل كافة التغييرات والأحداث الرقابية مصحوبة بـ IP المستخدم وحالتي السجل السابقة والجديدة.

---

## 7. مواصفات الربط مع محرك فحص العقوبات EFRM Screening
*(مستخلصة من الصفحات 2-6 من وثيقة المتطلبات الرسمية Requirements_UP_F.pdf)*

### نقاط البيانات الـ 24 المطلوبة (24 Screening Data Points):
| # | الحقل | الإلزامية | الوصف ومصدر البيانات في منصة تحصيل |
|---|---|---|---|
| 1 | `source_system` | إلزامي | كود النظام المرسل: `TAHSEEL` |
| 2 | `channel` | إلزامي | مسار الفحص: `ONBOARDING` أو `PERIODIC_REVIEW` |
| 3 | `institution_id` | إلزامي | كود المؤسسة المعرف لدى المزود: `KANJI` أو `TAHSEEL` |
| 4 | `entity_type` | إلزامي | للكيان: `ORGANIZATION` / للأطراف: `INDIVIDUAL` |
| 5 | `entity_relation` | إلزامي | `CUSTOMER`, `DIRECTOR`, `POC`, `AUTHORIZED_SIGNATORY` |
| 6 | `external_entity_id` | إلزامي للفحص الأساسي | كود المنشأة في تحصيل: `biller.biller_code` |
| 7 | `primary_entity_id` | إلزامي للفحص الثانوي | كود المنشأة الأساسية التي يتبع لها الطرف المفحوص |
| 8 | `relation_entity_id` | اختياري | معرّف الطرف في تحصيل: `party.id` |
| 9 | `name` | إلزامي | الاسم الكامل القانوني بالعربي أو الإنجليزي |
| 10 | `dob` | إلزامي للأفراد | تاريخ الميلاد بصيغة `YYYY-MM-DD` |
| 11 | `country` | إلزامي | رمز الدولة المعياري ISO Alpha-2 (مثل `YE`, `AE`, `SA`) |
| 12 | `address` | موصى به | العنوان الوطني / المسجل |
| 13 | `gender` | اختياري | الجنس للأفراد: `MALE` أو `FEMALE` |
| 14 | `entity_sub_type` | اختياري | التصنيف القانوني: `LIMITED_LIABILITY_COMPANY`, `SOLE_PROPRIETORSHIP` |
| 15 | `id_type1` | إلزامي | نوع الهوية: `REGISTRATION_ID`, `NATIONAL_ID`, `PASSPORT` |
| 16 | `id_value1` | إلزامي | رقم الهوية أو رقم السجل التجاري |
| 17 | `id_type2` | اختياري | نوع الهوية الثاني (مثل `TAX_ID`) |
| 18 | `id_value2` | اختياري | الرقم الضريبي / الزكوي |
| 19 | `id_type3` | اختياري | نوع الهوية الثالث (مثل `OTHER`) |
| 20 | `id_value3` | اختياري | رقم الترخيص المهني |
| 21 | `phone_no` | اختياري | رقم الهاتف |
| 22 | `email` | اختياري | البريد الإلكتروني |
| 23 | `metadata` | اختياري | كائن JSON يحتوي بيانات إضافية (النسبة، PEP، الفرع) |
| 24 | `client_request_id` | إلزامي | معرّف الطلب الفريد لمنع التكرار (Idempotency) |

### أ) حمولة فحص الكيان التجاري الأساسي (Primary Organization Screening Payload):
```json
{
  "entity_type": "ORGANIZATION",
  "entity_relation": "CUSTOMER",
  "external_entity_id": "BIL-YE-00109",
  "channel": "ONBOARDING",
  "source_system": "TAHSEEL",
  "institution_id": "KANJI",
  "client_request_id": "TAH-SCR-REQ-887102",
  "payload": {
    "name": "Al-Amal Commercial Trading LLC",
    "country": "YE",
    "address": "Zubairy Street, Sana'a, Yemen",
    "entity_sub_type": "LIMITED_LIABILITY_COMPANY",
    "id_type1": "REGISTRATION_ID",
    "id_value1": "CR-1029384",
    "id_type2": "TAX_ID",
    "id_value2": "TAX-998811",
    "id_type3": "OTHER",
    "id_value3": "LIC-776655",
    "phone_no": "+9671234567",
    "email": "compliance@alamal-trading.ye",
    "metadata": {
      "biller_code": "BIL-YE-00109",
      "sector": "COMMERCIAL",
      "mcc_code": "5411"
    }
  }
}
```

### ب) حمولة فحص الطرف المرتبط (Secondary Related Party Screening Payload):
```json
{
  "entity_type": "INDIVIDUAL",
  "entity_relation": "AUTHORIZED_SIGNATORY",
  "external_entity_id": "4b68e991-23a1-456b-bc54-e0c1f2345678",
  "primary_entity_id": "BIL-YE-00109",
  "relation_entity_id": "4b68e991-23a1-456b-bc54-e0c1f2345678",
  "channel": "ONBOARDING",
  "source_system": "TAHSEEL",
  "institution_id": "KANJI",
  "client_request_id": "TAH-SCR-REQ-887103",
  "payload": {
    "name": "Ahmed Mohamed Al-Shami",
    "dob": "1988-05-14",
    "country": "YE",
    "gender": "MALE",
    "address": "Hadda Street, Sana'a, Yemen",
    "id_type1": "NATIONAL_ID",
    "id_value1": "01010098765",
    "phone_no": "+967771234567",
    "email": "ahmed.shami@alamal-trading.ye",
    "metadata": {
      "role": "AUTHORIZED_SIGNATORY",
      "equity_percentage": 35.0,
      "is_ubo": true,
      "is_pep": false,
      "pep_position": ""
    }
  }
}
```

### ج) استجابة الفحص من محرك EFRM (Screening Response Schema):
```json
{
  "request_id": "8d8c7a62-7a9f-4f51-8c0e-3f0d1d0c91a2",
  "client_request_id": "TAH-SCR-REQ-887102",
  "external_entity_id": "BIL-YE-00109",
  "entity_type": "ORGANIZATION",
  "entity_relation": "CUSTOMER",
  "channel": "ONBOARDING",
  "source_system": "TAHSEEL",
  "institution_id": "KANJI",
  "decision": "ALLOW",
  "risk_band": "LOW",
  "overall_risk_score": 0,
  "matched": false,
  "hit_count": 0,
  "alert_generated": false,
  "case_generated": false,
  "case_id": null,
  "message": "Screening completed. No adverse matches detected.",
  "matches": [],
  "recommended_action": "ALLOW",
  "screened_at": "2026-10-13T12:30:10Z"
}
```

---

## 8. مواصفات محرك مراقبة المعاملات المالية اللحظية (Transaction Monitoring - EFRM)
*(مستخلصة من الصفحات 8-13 من وثيقة المتطلبات الرسمية)*

يدعم محرك EFRM تقييم مخاطر الحركات المالية عبر قنوات POS و ECOM و ATM بنمطين:
1. **SYNC (متزامن لحظي)**: يُرجع المحرك قرار السماح `ALLOW` أو الحظر `BLOCK` أو طلب التحقق `STEPUP` في نفس الـ HTTP Response خلال أجزاء من الثانية.
2. **ASYNC (غير متزامن)**: يستقبل المحرك المعاملة ويعيد `ACCEPTED`، ثم يُجري الفحص المعقد ويرسل القرار النهائي عبر **Webhook**.

### حمولة تقييم المعاملة المالية (ISO 8583 Data Fields Payload):
```json
{
  "payload": {
    "institution_id": "KANJI",
    "source_system": "CARD_TRANSACTION",
    "mode": "SYNC",
    "channel": "POS",
    "source_txn_id": "TXN-20261013-0001",
    "request_id": "REQ-SYNC-000001",
    "txnreqtrandate": "261013143000",
    "pan": "411111******1111",
    "processing_code": "010000",
    "amount": 25000.00,
    "stan": "123456",
    "local_time": "143000",
    "local_date": "1013",
    "mcc": "5411",
    "country_code": "887",
    "pos_entry_mode": "051",
    "pos_condition_code": "00",
    "pin_capture_code": "12",
    "acquiring_institution_id": "ACQ001",
    "forwarding_institution_id": "FWD001",
    "track2_data": "",
    "rrn": "626101300001",
    "authorization_id": "AUTH001",
    "response_code": "00",
    "terminal_id": "TERM001",
    "customer_id": "CUST000001",
    "merchant_name_location": "AL-AMAL SUPERMARKET SANA'A YE",
    "currency_code": "887"
  }
}
```

### قرارات المحرك المالية وإجراءات منصة تحصيل المقابلة:
| قرار EFRM | المعنى | الإجراء المطلوب من منصة تحصيل |
|---|---|---|
| `ALLOW` | حركة آمنة ومنخفضة المخاطر | إتمام وتنفيذ المعاملة المالية وقيد المبلغ |
| `BLOCK` | حركة احتيالية أو شديدة الخطورة | رفض المعاملة فورياً وإشعار المستخدم بنقطة البيع |
| `REVIEW` | حركة مشبوهة تستدعي التحقيق | تعليق مؤقت (Hold) أو مراجعة مسؤول الامتثال |
| `STEPUP` | تتطلب تحققاً إضافياً من حامل البطاقة | تفعيل التحقق الثنائي (إرسال رمز OTP أو بصمة) |

---

## 9. معالجة إشعارات الـ Webhooks والقرارات غير المتزامنة
*(مستخلصة من الصفحات 14-16 من وثيقة المتطلبات الرسمية)*

عند تشغيل النمط غير المتزامن أو عند إغلاق قضايا التحقيق من قبل محللي الامتثال، يرسل EFRM تنبيهات Webhook إلى منصة تحصيل.

### أ) حدث اتخاذ القرار غير المتزامن (`TRANSACTION_DECISION`):
```json
{
  "event_type": "TRANSACTION_DECISION",
  "event_id": "EVT-20261013-000001",
  "event_time": "2026-10-13T14:30:10Z",
  "institution_id": "KANJI",
  "source_system": "CARD_TRANSACTION",
  "fact": "card_txn",
  "mode": "ASYNC",
  "channel": "POS",
  "request_id": "REQ-ASYNC-000001",
  "source_txn_id": "TXN-20261013-0001",
  "decision": "BLOCK",
  "risk_score": 850,
  "risk_severity": "CRITICAL",
  "policy_code": "POLICY_HIGH_VALUE_THRESHOLD",
  "matched_rule_count": 2,
  "alert_generated": true,
  "case_created": true,
  "case_id": "CASE-20261013-000001",
  "signals": [
    {
      "rule_code": "POS_HIGH_VALUE_TXN",
      "signal_code": "POS_HIGH_VALUE_TXN",
      "severity": "CRITICAL",
      "score": 850,
      "description": "High value POS transaction detected"
    }
  ],
  "recommended_action": "BLOCK_TRANSACTION",
  "message": "Transaction blocked due to high risk"
}
```

### ب) الرد الإلزامي المتوقع من منصة تحصيل (Acknowledgement Response):
يجب أن ترجع منصة تحصيل الرد التالي فور استلام الـ Webhook مع كود `200 OK`:
```json
{
  "event_id": "EVT-20261013-000001",
  "source_txn_id": "TXN-20261013-0001",
  "status": "RECEIVED",
  "received_at": "2026-10-13T14:30:12Z",
  "message": "Decision received successfully"
}
```

### ج) حدث إغلاق وتحديث قضية التحقيق (`CASE_ACTION_UPDATE`):
```json
{
  "event_type": "CASE_ACTION_UPDATE",
  "event_id": "EVT-20261013-000002",
  "event_time": "2026-10-13T15:10:00Z",
  "institution_id": "KANJI",
  "source_system": "CARD_TRANSACTION",
  "source_txn_id": "TXN-20261013-0001",
  "case_id": "CASE-20261013-000001",
  "case_status": "CLOSED",
  "final_action": "CONFIRMED_FRAUD",
  "decision": "BLOCK",
  "remarks": "Analyst confirmed suspicious transaction pattern",
  "message": "Case closed and final action recorded"
}
```

---

## 10. دليل بناء واجهات الـ API لمنصة تحصيل (DRF Integration Guide)

### أ) ملف `serializers.py`:
```python
from rest_framework import serializers
from tahseel_aml.models import Biller, BillerParty, AMLTransactionMonitoringRecord

class BillerPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = BillerParty
        fields = [
            'id', 'role', 'full_name_ar', 'full_name_en',
            'id_type', 'id_number', 'date_of_birth', 'nationality', 'country_code', 'gender',
            'equity_percentage', 'is_pep', 'pep_position', 'fatca_status'
        ]

class BillerOnboardSerializer(serializers.ModelSerializer):
    parties = BillerPartySerializer(many=True)

    class Meta:
        model = Biller
        fields = [
            'id', 'biller_code', 'biller_type', 'name_ar', 'name_en',
            'sector', 'mcc_code', 'commercial_register_number',
            'license_number', 'tax_number', 'country_code', 'city', 'street_address', 'phone', 'email',
            'expected_monthly_volume', 'expected_monthly_count',
            'expected_avg_amount', 'max_single_amount',
            'status', 'risk_level', 'risk_score', 'requires_edd',
            'parties'
        ]
        read_only_fields = ['id', 'status', 'risk_level', 'risk_score', 'requires_edd']

    def create(self, validated_data):
        parties_data = validated_data.pop('parties', [])
        biller = Biller.objects.create(**validated_data)
        for party_data in parties_data:
            BillerParty.objects.create(biller=biller, **party_data)
        return biller
```

### ب) نقطة تسجيل وفحص المفوتر في `views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tahseel_aml.services import BillerComplianceService, KanjiEFRMClient, AuditService
from .serializers import BillerOnboardSerializer

class BillerOnboardAPIView(APIView):
    def post(self, request):
        serializer = BillerOnboardSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        biller = serializer.save(maker_user=request.user)

        # تهيئة عميل Kanji EFRM بموجب وثيقة المتطلبات
        client = KanjiEFRMClient(is_sandbox=True)
        service = BillerComplianceService(screening_client=client)

        # 1. التحقق من الهيكل القانوني
        service.validate_biller_structure(biller)

        # 2. فحص الكيان التجاري وفحص جميع الأطراف
        service.screen_biller_entity(biller, performed_by=request.user)
        service.screen_all_parties(biller, performed_by=request.user)

        # 3. احتساب وتقييم درجة المخاطر
        service.evaluate_and_update_risk(biller)

        # 4. توثيق العملية في سجل التدقيق غير القابل للتعديل
        AuditService().log_action(
            biller=biller,
            action="ONBOARDING_SCREENING_COMPLETED",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            "status": "SUCCESS",
            "biller_code": biller.biller_code,
            "risk_level": biller.risk_level,
            "risk_score": biller.risk_score,
            "requires_edd": biller.requires_edd,
            "compliance_status": biller.status,
            "message": "تم تسجيل المفوتر وفحص أطرافه في محرك العقوبات بنجاح"
        }, status=status.HTTP_201_CREATED)
```

### ج) نقطة استقبال تنبيهات الـ Webhooks من EFRM:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from tahseel_aml.services import EFRMWebhookProcessor

class EFRMWebhookReceiverAPIView(APIView):
    def post(self, request):
        response_data, status_code = EFRMWebhookProcessor.process_incoming_event(request.data)
        return Response(response_data, status=status_code)
```

---

## 11. لوحة التحكم الرقابية (Django Admin)

تم تزويد لوحة التحكم بأقفال أمان رقابية:
* **حظر الحذف الإداري:** لا يمكن لأي مستخدم (حتى الـ Superuser) حذف سجلات `AMLScreeningRecord` أو `AMLAuditLog` أو `AMLTransactionMonitoringRecord`.
* **شارات الحالة ومستوى المخاطر:** ألوان بصرية تميز الحالات (`ACTIVE`, `SUSPENDED`, `FROZEN`) والمخاطر (`LOW`, `MEDIUM`, `HIGH`, `PROHIBITED`).
* **شاشات استعراض الفحص والـ Webhooks:** عرض كامل الحمولات المستلمة والمرسلة (JSON) للرجوع إليها في أي تدقيق تفتيشي من البنك المركزي.

---

## 12. دليل النقل والتشغيل على النظام الرسمي (Deployment & Production Setup)

### الخطوة 1: نسخ مجلد التطبيق
انسخ مجلد `tahseel_aml/` بالكامل وضعه داخل المجلد الرئيسي لتطبيقات مشروع منصة تحصيل الرسمي.

### الخطوة 2: تفعيل التطبيق في `settings.py`
أضف التطبيق إلى قائمة `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... تطبيقات تحصيل الحالية ...
    'tahseel_aml.apps.TahseelAmlConfig',
]
```

### الخطوة 3: إضافة إعدادات الربط في `settings.py` (أو ملف `.env`)
قم بتعريف المتغيرات التالية لتمكين عميل `KanjiEFRMClient` من قراءتها تلقائياً:
```python
# ==============================================================================
# إعدادات منظومة الامتثال ومكافحة غسل الأموال (AML / EFRM Integration)
# ==============================================================================
import os

# روابط خدمات سيرفر FinFactory / RiskBrains
AML_SCREENING_URL = os.getenv("AML_SCREENING_URL", "http://10.225.119.170:8000/screening/v1")
AML_RULEENGINE_URL = os.getenv("AML_RULEENGINE_URL", "http://10.225.119.170:8083/ruleengine/v1")

# مفتاح المصادقة الرسمي (يتم تزويده من FinFactory)
AML_API_KEY = os.getenv("AML_API_KEY", "your-official-x-api-key")

# المعرفات المعتمدة لمؤسستنا
AML_INSTITUTION_ID = os.getenv("AML_INSTITUTION_ID", "ULTIMATE_PAY")
AML_SOURCE_SYSTEM = os.getenv("AML_SOURCE_SYSTEM", "TAHSEEL")

# وضع البيئة التجريبية: False للاتصال الحي بالسيرفر | True للمحاكاة بدون اتصال
AML_IS_SANDBOX = os.getenv("AML_IS_SANDBOX", "True").lower() in ("true", "1")
AML_TIMEOUT = int(os.getenv("AML_TIMEOUT", "10"))

# سر توقيع الـ Webhook (اختياري للتحقق الأمني من الإشعارات الواردة)
AML_WEBHOOK_SECRET = os.getenv("AML_WEBHOOK_SECRET", None)
```

### الخطوة 4: تفعيل مسارات الـ Webhook في `urls.py` الرئيسي للمشروع
في ملف `urls.py` الخاص بمشروع تحصيل العام:
```python
from django.urls import path, include

urlpatterns = [
    # ... مسارات تحصيل الحالية ...
    
    # مسار موديول الامتثال واستقبال الـ Webhook:
    # الرابط النهائي: https://tahseeltest.ultimate-pay.net/api/aml/webhook/
    path('api/aml/', include('tahseel_aml.urls')),
]
```

### الخطوة 5: تطبيق ترحيل قاعدة البيانات (Database Migrations)
```bash
# تطبيق الترحيلات المنشأة مسبقاً
python manage.py migrate tahseel_aml
```

### الخطوة 6: تشغيل الاختبارات للتأكد من سلامة التثبيت
```bash
python manage.py test tahseel_aml.tests.test_compliance
```
يجب أن تظهر النتيجة: `Ran 13 tests in 0.05s - OK`.

### الخطوة 7: التحقق من لوحة الإدارة
افتح لوحة الإدارة (`/admin/`) بحساب مسؤول، وتأكد من ظهور قسم **Tahseel AML/CFT Compliance** مع كامل الجداول وشارات الحالة والقيود الأمنية لعدم الحذف (Immutability).

