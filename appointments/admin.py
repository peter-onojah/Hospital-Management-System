from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Appointment, MedicalHistory, SMSAppointmentReminder

@admin.register(SMSAppointmentReminder)
class SMSAppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'reminder_datetime', 'status', 'created_at')
    list_filter = ('status', 'reminder_datetime')
    search_fields = ('appointment__appointment_id', 'message')
    readonly_fields = ('sent_at', 'api_response', 'created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Appointment Information', {
            'fields': ('appointment',)
        }),
        ('SMS Details', {
            'fields': ('reminder_datetime', 'message', 'status')
        }),
        ('Delivery Information', {
            'fields': ('sent_at', 'api_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )