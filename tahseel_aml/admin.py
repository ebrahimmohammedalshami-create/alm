"""
Django Admin Configuration for Tahseel AML (SOLID Structure)
لوحة التحكم الإدارية لنظام الامتثال ومكافحة غسل الأموال
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Biller,
    BillerParty,
    BillerDocument,
    AMLScreeningRecord,
    AMLAuditLog,
    AMLTransactionMonitoringRecord,
    AMLWebhookEvent
)


class BillerPartyInline(admin.TabularInline):
    model = BillerParty
    extra = 1
    fields = (
        'role', 'full_name_ar', 'id_type', 'id_number',
        'equity_percentage', 'is_ubo', 'is_pep', 'fatca_status', 'screening_decision'
    )


class BillerDocumentInline(admin.TabularInline):
    model = BillerDocument
    extra = 1
    fields = ('document_type', 'document_number', 'file', 'expiry_date', 'is_verified')


@admin.register(Biller)
class BillerAdmin(admin.ModelAdmin):
    list_display = (
        'biller_code', 'name_ar', 'biller_type', 'sector',
        'status_badge', 'risk_badge', 'requires_edd', 'created_at'
    )
    list_filter = ('biller_type', 'status', 'risk_level', 'requires_edd', 'sector')
    search_fields = ('biller_code', 'name_ar', 'name_en', 'commercial_register_number')
    readonly_fields = (
        'created_at', 'updated_at',
        'maker_user', 'maker_submitted_at',
        'checker_user', 'checker_approved_at'
    )
    inlines = [BillerPartyInline, BillerDocumentInline]

    fieldsets = (
        ("بيانات المنشأة الأساسية", {
            'fields': (
                'biller_code', 'biller_type', 'name_ar', 'name_en',
                'sector', 'mcc_code'
            )
        }),
        ("التراخيص والعناوين", {
            'fields': (
                'commercial_register_number', 'cr_expiry_date',
                'license_number', 'license_expiry_date', 'tax_number',
                'country', 'city', 'district', 'street_address', 'phone', 'email'
            )
        }),
        ("المؤشرات المالية والسلوكية المتوقعة (EFRM Profile)", {
            'fields': (
                'expected_monthly_volume', 'expected_monthly_count',
                'expected_avg_amount', 'max_single_amount'
            )
        }),
        ("تقييم مخاطر الامتثال (AML Risk Rating)", {
            'fields': (
                'risk_level', 'risk_score', 'requires_edd',
                'risk_rationale', 'last_risk_review_date', 'next_risk_review_date'
            )
        }),
        ("دورة الاعتماد والتدقيق (Maker / Checker)", {
            'fields': (
                'status', 'maker_user', 'maker_submitted_at',
                'checker_user', 'checker_approved_at', 'checker_notes'
            )
        }),
    )

    def status_badge(self, obj):
        colors = {
            'ACTIVE': 'green',
            'PENDING_CHECKER': 'orange',
            'SUSPENDED': 'red',
            'FROZEN': 'darkred',
            'DRAFT': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>')
    status_badge.short_description = "الحالة"

    def risk_badge(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'PROHIBITED': 'darkred'
        }
        color = colors.get(obj.risk_level, 'black')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{obj.get_risk_level_display()}</span>')
    risk_badge.short_description = "مستوى المخاطر"


@admin.register(BillerParty)
class BillerPartyAdmin(admin.ModelAdmin):
    list_display = (
        'full_name_ar', 'biller', 'role', 'equity_percentage',
        'is_ubo', 'is_pep', 'fatca_status', 'screening_decision'
    )
    list_filter = ('role', 'is_ubo', 'is_pep', 'fatca_status', 'screening_decision')
    search_fields = ('full_name_ar', 'full_name_en', 'id_number')


@admin.register(AMLScreeningRecord)
class AMLScreeningRecordAdmin(admin.ModelAdmin):
    list_display = ('searched_name', 'biller', 'decision', 'match_score', 'screening_system', 'created_at')
    list_filter = ('decision', 'screening_system', 'created_at')
    search_fields = ('searched_name', 'searched_id_number', 'biller__biller_code')
    readonly_fields = [f.name for f in AMLScreeningRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # فقط مسؤول الامتثال يمكنه إضافة قرار مراجعة لسجل POTENTIAL_MATCH
        return True


@admin.register(AMLAuditLog)
class AMLAuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'biller', 'performed_by', 'ip_display', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('biller__biller_code', 'performed_by__username', 'ip_address')
    readonly_fields = [f.name for f in AMLAuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def ip_display(self, obj):
        return obj.ip_address or '—'
    ip_display.short_description = 'عنوان IP'


@admin.register(AMLTransactionMonitoringRecord)
class AMLTransactionMonitoringRecordAdmin(admin.ModelAdmin):
    list_display = (
        'source_txn_id', 'biller', 'mode', 'channel',
        'pan_masked', 'amount', 'currency_code',
        'decision', 'risk_score', 'risk_severity', 'created_at'
    )
    list_filter = ('decision', 'mode', 'channel', 'risk_severity', 'alert_generated', 'created_at')
    search_fields = ('source_txn_id', 'request_id', 'rrn', 'pan_masked', 'biller__biller_code')
    readonly_fields = [f.name for f in AMLTransactionMonitoringRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AMLWebhookEvent)
class AMLWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'event_type', 'source_txn_id', 'decision', 'processed', 'event_time')
    list_filter = ('event_type', 'processed', 'decision', 'event_time')
    search_fields = ('event_id', 'source_txn_id', 'case_id')
    readonly_fields = [f.name for f in AMLWebhookEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

