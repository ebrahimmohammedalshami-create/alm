"""
KYC & KYB Document Model
مسؤولية النموذج: إدارة الملفات والمرفقات الثبوتية وتواريخ صلاحيتها (SRP)
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from .base import TimeStampedUUIDModel
from .choices import DocumentType
from .biller import Biller


def biller_document_upload_path(instance, filename):
    return f"biller_docs/{instance.biller.biller_code}/{instance.document_type}_{filename}"


class BillerDocument(TimeStampedUUIDModel):
    """
    وثائق المنشأة الثبوتية ومتابعة الصلاحية
    """
    biller = models.ForeignKey(
        Biller,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="المنشأة"
    )
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        verbose_name="نوع الوثيقة"
    )
    document_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="رقم الوثيقة"
    )
    file = models.FileField(
        upload_to=biller_document_upload_path,
        verbose_name="الملف المرفق"
    )
    issue_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الإصدار")
    expiry_date = models.DateField(blank=True, null=True, db_index=True, verbose_name="تاريخ الانتهاء")
    is_verified = models.BooleanField(default=False, verbose_name="تم التحقق")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="verified_documents",
        verbose_name="الموظف المتحقق"
    )
    verified_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ التحقق")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "وثيقة رسمية (KYC Document)"
        verbose_name_plural = "الوثائق الرسمية (KYC Documents)"

    def __str__(self):
        return f"{self.biller.biller_code} - {self.get_document_type_display()}"

    def is_expired(self) -> bool:
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def is_expiring_soon(self, days: int = 60) -> bool:
        if self.expiry_date:
            today = timezone.now().date()
            return today <= self.expiry_date <= (today + timezone.timedelta(days=days))
        return False
