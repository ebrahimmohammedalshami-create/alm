"""
AML & Tahseel Choices and Constants
Separation of Concerns: Value Objects & Constants definition
"""

from django.db import models


class BillerType(models.TextChoices):
    """نوع المفوتر / الكيان القانوني"""
    GOVERNMENT = 'GOVERNMENT', 'حكومي (Government)'
    MERCHANT = 'MERCHANT', 'تاجر / مؤسسة فردية (Merchant / Sole Proprietorship)'
    PRIVATE_COMPANY = 'PRIVATE_COMPANY', 'شركة خاصة (Private Company)'
    MIXED = 'MIXED', 'مختلط (Mixed / Semi-Government)'


class SectorType(models.TextChoices):
    """القطاع الاقتصادي"""
    COMMERCIAL = 'COMMERCIAL', 'تجاري'
    SERVICE = 'SERVICE', 'خدمي'
    FINANCIAL = 'FINANCIAL', 'مالي ومصرفي'
    TELECOM = 'TELECOM', 'اتصالات وتقنية'
    EDUCATION = 'EDUCATION', 'تعليمي'
    HEALTHCARE = 'HEALTHCARE', 'صحي'
    UTILITIES = 'UTILITIES', 'خدمات عامة (كهرباء / مياه)'
    CHARITY = 'CHARITY', 'منظمات غير ربحية / خيرية'
    OTHER = 'OTHER', 'أخرى'


class BillerStatus(models.TextChoices):
    """حالة المفوتر في النظام"""
    DRAFT = 'DRAFT', 'مسودة (قيد الإدخال)'
    PENDING_MAKER = 'PENDING_MAKER', 'قيد مراجعة المدخل (Maker)'
    PENDING_CHECKER = 'PENDING_CHECKER', 'قيد موافقة المشرف (Checker)'
    ACTIVE = 'ACTIVE', 'نشط ومعتمد'
    SUSPENDED = 'SUSPENDED', 'معلق (بقرار رقابي أو AML)'
    FROZEN = 'FROZEN', 'مجمد بالكامل (Sanctions / AML Freeze)'
    REJECTED = 'REJECTED', 'مرفوض'


class RiskLevel(models.TextChoices):
    """مستوى مخاطر مكافحة غسل الأموال (AML Risk Level)"""
    LOW = 'LOW', 'منخفض (Low)'
    MEDIUM = 'MEDIUM', 'متوسط (Medium)'
    HIGH = 'HIGH', 'مرتفع (High - يستلزم عناية واجبة مشددة EDD)'
    PROHIBITED = 'PROHIBITED', 'محظور التعامل'


class PartyRole(models.TextChoices):
    """صفة الطرف المرتبط بالمنشأة"""
    OWNER = 'OWNER', 'مالك (Owner)'
    PARTNER = 'PARTNER', 'شريك (Partner)'
    AUTHORIZED_SIGNATORY = 'AUTHORIZED_SIGNATORY', 'مفوض بالتوقيع (Authorized Signatory)'
    BOARD_MEMBER = 'BOARD_MEMBER', 'عضو مجلس إدارة (Board Member)'
    UBO = 'UBO', 'المستفيد الحقيقي النهائي (Ultimate Beneficial Owner)'


class IDType(models.TextChoices):
    """نوع الهوية الشخصية"""
    NATIONAL_ID = 'NATIONAL_ID', 'بطاقة شخصية / رقم وطني'
    PASSPORT = 'PASSPORT', 'جواز سفر'
    FAMILY_CARD = 'FAMILY_CARD', 'بطاقة عائلية'
    RESIDENCE_PERMIT = 'RESIDENCE_PERMIT', 'إقامة'


class FATCAStatus(models.TextChoices):
    """حالة الامتثال لقانون الامتثال الضريبي للحسابات الأجنبية (FATCA)"""
    NO = 'NO', 'غير خاضع'
    US_PASSPORT = 'US_PASSPORT', 'يحمل جواز سفر أمريكي'
    US_GREENCARD = 'US_GREENCARD', 'يحمل البطاقة الخضراء (Green Card)'


class PEPRiskLevel(models.TextChoices):
    """مستوى خطورة الشخص المعرض سياسياً (PEP)"""
    CRITICAL = 'CRITICAL', 'حرج (Critical)'
    HIGH = 'HIGH', 'مرتفع (High)'
    MEDIUM = 'MEDIUM', 'متوسط (Medium)'
    LOW = 'LOW', 'منخفض (Low)'


class ScreeningDecision(models.TextChoices):
    """نتيجة فحص قوائم الحظر والعقوبات"""
    NO_MATCH = 'NO_MATCH', 'سليم - لا يوجد تطابق (Clear)'
    POTENTIAL_MATCH = 'POTENTIAL_MATCH', 'اشتباه / تطابق محتمل (Pending Review)'
    CONFIRMED_MATCH = 'CONFIRMED_MATCH', 'تطابق مؤكد - قائمة سوداء (Confirmed Hit)'
    FALSE_POSITIVE = 'FALSE_POSITIVE', 'تطابق خاطئ بعد التحقيق (False Positive)'


class Gender(models.TextChoices):
    """الجنس (مطابق لمتطلبات EFRM / Kanji)"""
    MALE = 'MALE', 'ذكر (Male)'
    FEMALE = 'FEMALE', 'أنثى (Female)'


class ScreeningEntityType(models.TextChoices):
    """نوع الكيان المفحوص في محرك العقوبات (EFRM Entity Type)"""
    ORGANIZATION = 'ORGANIZATION', 'منشأة / شركة (Organization)'
    MERCHANT = 'MERCHANT', 'تاجر (Merchant)'
    LIMITED_LIABILITY_COMPANY = 'LIMITED_LIABILITY_COMPANY', 'شركة ذات مسؤولية محدودة'
    NPO_NGO = 'NPO_NGO', 'منظمة غير ربحية / خيرية'
    INDIVIDUAL = 'INDIVIDUAL', 'فرد (Individual)'


class EntityRelation(models.TextChoices):
    """علاقة الكيان بالمنظومة (Entity Relation في EFRM)"""
    CUSTOMER = 'CUSTOMER', 'عميل أساسي (Customer)'
    DIRECTOR = 'DIRECTOR', 'مدير / عضو إدارة (Director)'
    POC = 'POC', 'نقطة اتصال (Point of Contact)'
    AUTHORIZED_SIGNATORY = 'AUTHORIZED_SIGNATORY', 'مفوض بالتوقيع'


class ScreeningRiskBand(models.TextChoices):
    """نطاق الخطورة الصادر من محرك AML (Risk Band)"""
    LOW = 'LOW', 'منخفض (Low)'
    MEDIUM = 'MEDIUM', 'متوسط (Medium)'
    HIGH = 'HIGH', 'مرتفع (High)'
    CRITICAL = 'CRITICAL', 'حرج (Critical)'


class TxnMode(models.TextChoices):
    """نمط فحص العمليات المالية (EFRM Mode)"""
    SYNC = 'SYNC', 'متزامن فوري (Synchronous)'
    ASYNC = 'ASYNC', 'غير متزامن (Asynchronous)'


class TxnChannel(models.TextChoices):
    """قناة العملية المالية (Transaction Channel)"""
    POS = 'POS', 'نقاط البيع (POS)'
    ECOM = 'ECOM', 'التجارة الإلكترونية (E-Commerce)'
    ATM = 'ATM', 'أجهزة الصراف الآلي (ATM)'


class TxnDecision(models.TextChoices):
    """قرار فحص المعاملة المالية من محرك EFRM"""
    ALLOW = 'ALLOW', 'سماح بالعملية (Allow / Approve)'
    BLOCK = 'BLOCK', 'حظر العملية (Block / Decline)'
    REVIEW = 'REVIEW', 'مراجعة يدوية (Review / Hold)'
    STEPUP = 'STEPUP', 'تحقق إضافي (Step-Up / OTP / Challenge)'


class TxnActionType(models.TextChoices):
    """نوع الإجراء المطلوب بعد فحص المعاملة"""
    RETURN_SYNC_RESPONSE = 'RETURN_SYNC_RESPONSE', 'إرجاع رد متزامن فوري'
    SEND_WEBHOOK = 'SEND_WEBHOOK', 'إرسال تنبيه Webhook'
    CREATE_ALERT = 'CREATE_ALERT', 'إنشاء تنبيه رقابي'
    CREATE_CASE = 'CREATE_CASE', 'فتح قضية تحقيق (Case)'
    STEPUP_REQUIRED = 'STEPUP_REQUIRED', 'طلب تحقق إضافي من العميل'
    BLOCK_TRANSACTION = 'BLOCK_TRANSACTION', 'رفض المعاملة المالية'
    MARK_FOR_REVIEW = 'MARK_FOR_REVIEW', 'تحديد للمراجعة'
    LOG_ONLY = 'LOG_ONLY', 'تسجيل فقط بدون إجراء'


class DocumentType(models.TextChoices):
    """نوع الوثيقة الثبوتية (KYB/KYC)"""
    COMMERCIAL_REGISTER = 'COMMERCIAL_REGISTER', 'السجل التجاري'
    PROFESSIONAL_LICENSE = 'PROFESSIONAL_LICENSE', 'الترخيص المهني / مزاولة المهنة'
    ARTICLES_OF_INCORPORATION = 'ARTICLES_OF_INCORPORATION', 'عقد التأسيس والنظام الأساسي'
    SIGNATURE_AUTHORIZATION = 'SIGNATURE_AUTHORIZATION', 'تفويض التوقيع المعتمد'
    OWNER_NATIONAL_ID = 'OWNER_NATIONAL_ID', 'الهوية الشخصية للمالك/الشريك'
    TAX_CERTIFICATE = 'TAX_CERTIFICATE', 'الرقم الضريبي / الزكوي'
    OTHER = 'OTHER', 'وثائق أخرى داعمة'

