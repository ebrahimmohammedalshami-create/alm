"""
Biller Model (Tahseel Entity)
مسؤولية النموذج: تمثيل بيانات الكيان المفوتر فقط (SRP)
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import TimeStampedUUIDModel
from .choices import BillerType, SectorType, BillerStatus, RiskLevel


class Biller(TimeStampedUUIDModel):
    """
    سجل المنشأة المفوترة (Biller Entity) في منصة تحصيل
    """
    # معرف المنشأة في نظام تحصيل / Ultimate Pay
    biller_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="رمز المفوتر (Biller Code)"
    )
    biller_type = models.CharField(
        max_length=30,
        choices=BillerType.choices,
        db_index=True,
        verbose_name="نوع الكيان القانوني"
    )

    # الأسماء باللغتين
    name_ar = models.CharField(max_length=255, db_index=True, verbose_name="اسم المنشأة بالعربي")
    name_en = models.CharField(max_length=255, db_index=True, verbose_name="اسم المنشأة بالإنجليزي")

    # القطاع ورمز MCC (ISO 18245)
    sector = models.CharField(
        max_length=30,
        choices=SectorType.choices,
        default=SectorType.COMMERCIAL,
        verbose_name="القطاع الاقتصادي"
    )
    mcc_code = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        verbose_name="رمز فئة التاجر (MCC)",
        help_text="Merchant Category Code (ISO 18245)"
    )

    # بيانات السجل التجاري والترخيص المهني
    commercial_register_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="رقم السجل التجاري"
    )
    cr_expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ انتهاء السجل التجاري"
    )
    license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="رقم الترخيص المهني / النشاط"
    )
    license_expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ انتهاء الترخيص"
    )
    tax_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="الرقم الضريبي / الزكوي"
    )

    # العنوان الوطني والاتصال
    country = models.CharField(max_length=100, default="Yemen", verbose_name="الدولة")
    country_code = models.CharField(max_length=2, default="YE", verbose_name="رمز الدولة (ISO Alpha-2)", help_text="مثال: YE, AE, SA")
    entity_sub_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="التصنيف القانوني الفرعي",
        help_text="مثال: LIMITED_LIABILITY_COMPANY, SOLE_PROPRIETORSHIP, JOINT_VENTURE"
    )
    city = models.CharField(max_length=100, verbose_name="المدينة / المحافظة")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="المديرية / الحي")
    street_address = models.CharField(max_length=255, verbose_name="العنوان التفصيلي")
    phone = models.CharField(max_length=50, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")

    # المؤشرات السلوكية والمالية المتوقعة لمراقبة المعاملات EFRM
    expected_monthly_volume = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="حجم المبيعات الشهري المتوقع"
    )
    expected_monthly_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الحركات الشهري المتوقع"
    )
    expected_avg_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="متوسط قيمة الحركة المتوقعة"
    )
    max_single_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="الحد الأقصى المسموح للحركة الواحدة"
    )

    # تصنيف مخاطر مكافحة غسل الأموال (AML Risk Profiling)
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
        db_index=True,
        verbose_name="تصنيف مخاطر العميل (AML Risk Rating)"
    )
    risk_score = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="درجة المخاطر (0-100)"
    )
    risk_rationale = models.TextField(
        blank=True,
        null=True,
        verbose_name="مبررات وملاحظات تقييم المخاطر"
    )
    requires_edd = models.BooleanField(
        default=False,
        verbose_name="يتطلب عناية واجبة مشددة (Requires EDD)"
    )
    last_risk_review_date = models.DateField(blank=True, null=True, verbose_name="تاريخ آخر مراجعة مخاطر")
    next_risk_review_date = models.DateField(blank=True, null=True, verbose_name="تاريخ المراجعة القادمة")

    # مسار الاعتماد والتدقيق المزدوج (Maker / Checker Workflow)
    status = models.CharField(
        max_length=30,
        choices=BillerStatus.choices,
        default=BillerStatus.DRAFT,
        db_index=True,
        verbose_name="حالة المنشأة"
    )
    maker_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="biller_maker_records",
        blank=True,
        null=True,
        verbose_name="المدخل (Maker)"
    )
    maker_submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الإرسال للاعتماد")
    checker_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="biller_checker_records",
        blank=True,
        null=True,
        verbose_name="المعتمد (Checker)"
    )
    checker_approved_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الاعتماد")
    checker_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات المعتمد")

    class Meta:
        verbose_name = "منشأة مفوترة (Biller)"
        verbose_name_plural = "المنشآت المفوترة (Billers)"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['biller_code', 'status']),
            models.Index(fields=['biller_type', 'risk_level']),
        ]

    def __str__(self):
        return f"{self.biller_code} - {self.name_ar} ({self.get_biller_type_display()})"

    def total_equity_percentage(self) -> Decimal:
        """إجمالي نسب ملكية الشركاء والمالكين"""
        from .choices import PartyRole
        total = self.parties.filter(
            role__in=[PartyRole.OWNER, PartyRole.PARTNER]
        ).aggregate(
            total_share=models.Sum('equity_percentage')
        )['total_share'] or Decimal('0.00')
        return total

    def has_pep_parties(self) -> bool:
        """هل يوجد أي شخص معرض سياسياً؟"""
        return self.parties.filter(is_pep=True).exists()
