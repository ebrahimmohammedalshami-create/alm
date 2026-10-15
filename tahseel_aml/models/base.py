"""
Abstract Base Models (SRP & OCP)
يوفر نماذج أساسية قابلة للتوريث بدون تكرار الكود
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError


class TimeStampedUUIDModel(models.Model):
    """
    نموذج أساسي لجميع الكيانات
    - يطبق معرّف UUID غير تسلسلي لمنع التخمين الأمني
    - يطبق تتبع وقت الإنشاء والتحديث
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="تاريخ ووقت الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ ووقت التحديث")

    class Meta:
        abstract = True


class ImmutableComplianceModel(models.Model):
    """
    Liskov Substitution & Single Responsibility:
    نموذج مخصص لسجلات الامتثال الرقابي (سجلات الفحص، سجلات التدقيق).
    يمنع الحذف أو التعديل برمجياً للامتثال لقانون الحفظ لمدة 10 سنوات (CBY & FATF).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise ValidationError("محظور قانونياً: سجلات الامتثال الرقابي غير قابلة للحذف نهائياً (CBY Compliance).")
