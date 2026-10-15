"""
Immutable Compliance Models (Screening & Audit Trail)
مسؤولية النموذج: حفظ السجلات الرقابية غير القابلة للتعديل أو الحذف (SRP & LSP)
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .base import ImmutableComplianceModel
from .choices import ScreeningDecision, ScreeningRiskBand
from .biller import Biller
from .party import BillerParty


class AMLScreeningRecord(ImmutableComplianceModel):
    """
    سجل فحص قوائم الحظر والعقوبات (Append-Only / Immutable)
    مطابق تماماً لمواصفات EFRM / Kanji الواردة في وثيقة Requirements_UP_F.pdf
    """
    biller = models.ForeignKey(
        Biller,
        on_delete=models.PROTECT,
        related_name="screening_records",
        verbose_name="المنشأة المفوترة"
    )
    party = models.ForeignKey(
        BillerParty,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="screening_records",
        verbose_name="الطرف المفحوص"
    )
    # معرفات الربط والتتبع (Tracing & Idempotency)
    client_request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="رقم طلب العميل (Client Request ID)"
    )
    provider_request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="رقم طلب مزود الخدمة (EFRM Request ID)"
    )

    searched_name = models.CharField(max_length=255, verbose_name="الاسم المدخل")
    searched_id_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الهوية المدخل")
    screening_system = models.CharField(max_length=100, default="Kanji EFRM / Watchlist Engine", verbose_name="محرك الفحص")

    # نتائج الفحص ومستوى الخطورة
    decision = models.CharField(max_length=30, choices=ScreeningDecision.choices, db_index=True, verbose_name="النتيجة")
    risk_band = models.CharField(
        max_length=20,
        choices=ScreeningRiskBand.choices,
        default=ScreeningRiskBand.LOW,
        verbose_name="نطاق الخطورة (Risk Band)"
    )
    overall_risk_score = models.PositiveIntegerField(default=0, verbose_name="درجة الخطورة الإجمالية (0-1000)")
    match_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="أعلى نسبة تطابق %")

    # تفاصيل التطابقات والحالات
    matched = models.BooleanField(default=False, verbose_name="يوجد تطابق")
    hit_count = models.PositiveIntegerField(default=0, verbose_name="عدد التطابقات (Hit Count)")
    matched_lists = models.TextField(blank=True, null=True, verbose_name="القوائم المتطابقة (OFAC, UN, ...)")

    # إجراءات التنبيه والقضايا
    alert_generated = models.BooleanField(default=False, verbose_name="تم إنشاء تنبيه (Alert)")
    case_generated = models.BooleanField(default=False, verbose_name="تم فتح قضية تحقيق (Case)")
    case_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name="رقم القضية (Case ID)")
    recommended_action = models.CharField(max_length=50, blank=True, null=True, verbose_name="الإجراء الموصى به")
    screened_at = models.DateTimeField(blank=True, null=True, verbose_name="توقيت الفحص الفعلي لدى المزود")

    raw_request_payload = models.JSONField(verbose_name="نص الطلب المرسل (JSON)")
    raw_response_payload = models.JSONField(verbose_name="نص الرد المستلم (JSON)")

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="مسؤول الامتثال"
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ المراجعة")
    review_justification = models.TextField(blank=True, null=True, verbose_name="مبررات القرار")

    class Meta:
        verbose_name = "سجل فحص عقوبات (Screening Log)"
        verbose_name_plural = "سجلات فحص العقوبات (Screening Logs)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.searched_name} - {self.get_decision_display()}"

    def save(self, *args, **kwargs):
        if self.pk and AMLScreeningRecord.objects.filter(pk=self.pk).exists():
            existing = AMLScreeningRecord.objects.get(pk=self.pk)
            if existing.decision != ScreeningDecision.POTENTIAL_MATCH and not kwargs.get('force_update', False):
                raise ValidationError("سجلات فحص العقوبات غير قابلة للتعديل قانونياً (Immutable Compliance Record).")
        super().save(*args, **kwargs)


class AMLAuditLog(ImmutableComplianceModel):
    """
    سجل التدقيق الرقابي والأمني (Audit Trail)
    محفوظ لمدة 10 سنوات على الأقل
    """
    biller = models.ForeignKey(
        Biller,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        verbose_name="المنشأة"
    )
    action_type = models.CharField(max_length=50, db_index=True, verbose_name="نوع الحدث")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="المستخدم"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")
    user_agent = models.CharField(max_length=255, blank=True, null=True, verbose_name="المتصفح")

    previous_state = models.JSONField(blank=True, null=True, verbose_name="الحالة السابقة")
    new_state = models.JSONField(blank=True, null=True, verbose_name="الحالة الجديدة")
    change_reason = models.TextField(blank=True, null=True, verbose_name="السبب")

    class Meta:
        verbose_name = "سجل التدقيق الرقابي (AML Audit Log)"
        verbose_name_plural = "سجلات التدقيق الرقابي (AML Audit Logs)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type} on {self.biller.biller_code} by {self.performed_by}"

    def save(self, *args, **kwargs):
        if self.pk and AMLAuditLog.objects.filter(pk=self.pk).exists():
            raise ValidationError("سجلات التدقيق الرقابي غير قابلة للتعديل نهائياً.")
        super().save(*args, **kwargs)
