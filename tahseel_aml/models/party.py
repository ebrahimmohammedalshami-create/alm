"""
BillerParty Model (Owners, Partners, UBO, Signatories)
مسؤولية النموذج: تمثيل بيانات الأطراف المرتبطة وفحوصات الامتثال (SRP)
"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import TimeStampedUUIDModel
from .choices import PartyRole, IDType, FATCAStatus, PEPRiskLevel, ScreeningDecision, Gender
from .biller import Biller


class BillerParty(TimeStampedUUIDModel):
    """
    سجل الشركاء والمالكين والمفوضين والمستفيدين الحقيقيين (UBO)
    """
    biller = models.ForeignKey(
        Biller,
        on_delete=models.CASCADE,
        related_name="parties",
        verbose_name="المنشأة التابع لها"
    )
    role = models.CharField(
        max_length=30,
        choices=PartyRole.choices,
        db_index=True,
        verbose_name="صفة الطرف"
    )

    # الأسماء الرباعية
    full_name_ar = models.CharField(max_length=255, db_index=True, verbose_name="الاسم الكامل بالعربي")
    full_name_en = models.CharField(max_length=255, db_index=True, verbose_name="الاسم الكامل بالإنجليزي")

    # بيانات الهوية
    id_type = models.CharField(
        max_length=30,
        choices=IDType.choices,
        default=IDType.NATIONAL_ID,
        verbose_name="نوع الهوية"
    )
    id_number = models.CharField(max_length=50, db_index=True, verbose_name="رقم الهوية")
    id_issue_date = models.DateField(blank=True, null=True, verbose_name="تاريخ إصدار الهوية")
    id_expiry_date = models.DateField(blank=True, null=True, verbose_name="تاريخ انتهاء الهوية")

    # البيانات الشخصية (مطابقة لمتطلبات EFRM / Kanji)
    nationality = models.CharField(max_length=100, default="Yemeni", verbose_name="الجنسية")
    country_code = models.CharField(max_length=2, default="YE", verbose_name="رمز الدولة (ISO Alpha-2)", help_text="مثال: YE, AE, SA")
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        null=True,
        verbose_name="الجنس (Gender)"
    )
    date_of_birth = models.DateField(verbose_name="تاريخ الميلاد")
    national_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="العنوان الوطني")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")

    # الملكية والمستفيد الحقيقي (UBO)
    equity_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="نسبة الملكية / الحصة (%)"
    )
    is_ubo = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="مستفيد حقيقي نهائي (UBO)"
    )

    # الامتثال الضريبي الأمريكي (FATCA)
    fatca_status = models.CharField(
        max_length=20,
        choices=FATCAStatus.choices,
        default=FATCAStatus.NO,
        verbose_name="حالة FATCA"
    )
    us_tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="الرقم الضريبي الأمريكي (SSN / ITIN)"
    )

    # الأشخاص المعرضون سياسياً (PEP)
    is_pep = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="شخص معرض سياسياً (PEP)"
    )
    pep_position = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="المنصب السياسي / الحكومي"
    )
    pep_entity = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="الجهة التابع لها المنصب"
    )
    pep_risk_severity = models.CharField(
        max_length=20,
        choices=PEPRiskLevel.choices,
        blank=True,
        null=True,
        verbose_name="درجة خطورة المنصب السياسي"
    )

    # حالة فحص قوائم الحظر والعقوبات
    screening_decision = models.CharField(
        max_length=30,
        choices=ScreeningDecision.choices,
        default=ScreeningDecision.NO_MATCH,
        db_index=True,
        verbose_name="قرار الفحص الرقابي"
    )
    last_screened_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاريخ ووقت آخر فحص رقابي"
    )

    class Meta:
        verbose_name = "طرف مرتبط (مالك / شريك / مفوض)"
        verbose_name_plural = "الأطراف المرتبطة (Biller Parties)"
        indexes = [
            models.Index(fields=['biller', 'role']),
            models.Index(fields=['id_number', 'nationality']),
            models.Index(fields=['is_pep', 'is_ubo']),
        ]

    def __str__(self):
        return f"{self.full_name_ar} ({self.get_role_display()}) - {self.equity_percentage}%"

    def clean(self):
        """
        تفويض التحقق إلى المدقق المخصص للامتثال لمبدأ المسؤولية الواحدة (SRP)
        """
        from ..validators import PartyComplianceValidator
        validator = PartyComplianceValidator()
        validator.validate(self)

    def save(self, *args, **kwargs):
        # تصنيف المستفيد الحقيقي (UBO) تلقائياً لمن يملك 25% أو أكثر
        if self.equity_percentage and self.equity_percentage >= Decimal('25.00'):
            self.is_ubo = True
        self.full_clean()
        super().save(*args, **kwargs)
