from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin, TabularInline as UnfoldTabularInline

from .models import (
    FaultCategory, Symptom, Part, Device,
    ServiceTicket, Attachment, TicketComment
)


@admin.register(FaultCategory)
class FaultCategoryAdmin(UnfoldModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Symptom)
class SymptomAdmin(UnfoldModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']


@admin.register(Part)
class PartAdmin(UnfoldModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Device)
class DeviceAdmin(UnfoldModelAdmin):
    list_display = ['serial_no', 'family', 'model_name', 'customer_name', 'created_at']
    list_filter = ['family']
    search_fields = ['serial_no', 'customer_name', 'model_name']
    readonly_fields = ['created_at', 'updated_at']


class AttachmentInline(UnfoldTabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['original_name', 'size_bytes', 'mime_type', 'uploaded_by', 'uploaded_at']
    fields = ['kind', 'title', 'file', 'original_name', 'size_bytes', 'uploaded_by', 'uploaded_at']


class CommentInline(UnfoldTabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ['author', 'created_at']
    fields = ['author', 'body', 'is_internal', 'created_at']


@admin.register(ServiceTicket)
class ServiceTicketAdmin(UnfoldModelAdmin):
    list_display = [
        'code', 'device', 'subject', 'fault_category',
        'priority', 'status', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'priority', 'fault_category', 'device__family']
    search_fields = ['code', 'subject', 'device__serial_no', 'device__customer_name']
    readonly_fields = ['code', 'created_by', 'created_at', 'updated_at', 'closed_at']
    filter_horizontal = ['parts_used']
    inlines = [AttachmentInline, CommentInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
