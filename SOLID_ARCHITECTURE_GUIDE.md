# دليل تطبيق مبادئ SOLID في نظام Tahseel AML

تمت إعادة هيكلة النظام وتصميمه بدقة متناهية وفق مبادئ **SOLID** الخمسة لتسهيل صيانته واختباره وتوسيعه مستقبلاً على السيرفر:

---

## 1. تطبيق مبادئ SOLID بالتفصيل:

### S - Single Responsibility Principle (مبدأ المسؤولية الواحدة)
- **كل نموذج (Model) له مسؤولية واحدة فقط**:
  - `Biller`: بيانات الكيان المفوتر والمؤشرات المالية فقط (`models/biller.py`).
  - `BillerParty`: بيانات الشركاء والملاك والمفوضين (`models/party.py`).
  - `BillerDocument`: إدارة المرفقات وصلاحيتها فقط (`models/document.py`).
  - `AMLScreeningRecord` & `AMLAuditLog`: سجلات الفحص والتدقيق القانونية (`models/screening.py`).
- تم فصل **التحقق من صحة البيانات (Validation)** و **احتساب المخاطر (Risk Scoring)** إلى مجلدات مستقلة (`validators/` و `services/`) بدلاً من حشوها داخل كلاس النموذج.

### O - Open/Closed Principle (مبدأ المفتوح والمغلق)
- الكود مفتوح للتوسع، ومغلق أمام التعديل.
- إذا أردت إضافة نوع كيان جديد في المستقبل (مثلاً: كيان أجنبي `FOREIGN_COMPANY`)، لا تعدل في الكود القديم؛ فقط أنشئ كلاس تحقق جديد يرث من `IBillerValidator` وسيعمل النظام فوراً دون أي تعديل على الكود القائم.
- خوارزميات تقييم المخاطر تعتمد على `IRiskCalculationStrategy` بنمط التصميم (**Strategy Pattern**)، مما يمكنك من تغيير طريقة حساب المخاطر دون لمس نماذج البيانات.

### L - Liskov Substitution Principle (مبدأ إحلال ليسكوف)
- تم بناء الكلاسات الأساسية:
  - `TimeStampedUUIDModel`: لجميع الجداول القابلة للتحديث الطبيعي.
  - `ImmutableComplianceModel`: لجميع جداول التدقيق والامتثال القانونية، حيث تمنع الحذف نهائياً وتضمن عدم كسر العقود القانونية عند استدعاء أي كائن مشتق منها.

### I - Interface Segregation Principle (مبدأ فصل الواجهات)
- بدلاً من واجهة واحدة ضخمة تفحص كل شيء، تم تقسيم الواجهات في `interfaces/__init__.py`:
  - `IBillerValidator`: خاصة بالكيانات.
  - `IPartyValidator`: خاصة بالأفراد والشركاء.
  - `IRiskCalculationStrategy`: خاصة بمحرك احتساب المخاطر.
  - `ISanctionsScreeningClient`: خاصة بالاتصال مع محرك الفحص الخارجي (Kanji / API).
  - `IAuditLogger`: خاصة بتوثيق سجلات التدقيق.

### D - Dependency Inversion Principle (مبدأ عكس التبعية)
- الفئات العليا مثل `BillerComplianceService` تعتمد على واجهات مجردة (`Interfaces`) وليس على تطبيقات محددة (`Concrete Classes`).
- يمكنك بسهولة تمرير محرك فحص وهمي (**Mock Client**) أثناء الاختبارات بدون الحاجة للاتصال الفعلي بالـ API الخارجي.

---

## 2. الهيكل الشجري للمشروع (SOLID Project Structure):

```text
tahseel_aml/
│
├── interfaces/             # واجهات مجردة (Abstractions & Protocols)
│   └── __init__.py         # IBillerValidator, IRiskCalculationStrategy, ISanctionsScreeningClient...
│
├── models/                 # نماذج البيانات منفصلة المسؤوليات (SRP)
│   ├── choices.py          # الثوابت والخيارات (Enums)
│   ├── base.py             # النماذج التجريدية (LSP)
│   ├── biller.py           # نموذج المفوتر (Biller)
│   ├── party.py            # نموذج الشركاء والـ UBO والـ PEP
│   ├── document.py         # نموذج الوثائق والمستندات
│   ├── screening.py        # سجلات الفحص والتدقيق غير القابلة للتعديل
│   └── __init__.py         # تصدير النماذج الموحدة
│
├── validators/             # مدققات قواعد العمل المنفصلة (OCP & SRP)
│   └── __init__.py         # GovernmentBillerValidator, MerchantBillerValidator, PrivateCompany...
│
└── services/               # خدمات العمليات وتكامل الأنظمة (DIP)
    └── __init__.py         # BillerComplianceService, StandardRiskCalculationStrategy, AuditService
```

---

## 3. طريقة الاستخدام والنقل إلى السيرفر:

1. انسخ مجلد `tahseel_aml` بالكامل وضعه داخل مشروع Django على سيرفرك.
2. أضف `'tahseel_aml'` إلى قائمة `INSTALLED_APPS` في `settings.py`.
3. نفذ أمر الترحيل:
   ```bash
   python manage.py makemigrations tahseel_aml
   python manage.py migrate
   ```
