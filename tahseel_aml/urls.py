"""
URL Configuration for Tahseel AML App
مسارات الربط الشبكي لموديول الامتثال ومكافحة غسل الأموال
"""

from django.urls import path
from .views import aml_webhook_view, aml_health_check_view

app_name = 'tahseel_aml'

urlpatterns = [
    # رابط استقبال إشعارات الـ Webhook من محرك EFRM
    # الرابط الكامل: https://tahseeltest.ultimate-pay.net/api/aml/webhook/
    path('webhook/', aml_webhook_view, name='webhook'),

    # فحص صحة الموديول
    path('health/', aml_health_check_view, name='health'),
]
