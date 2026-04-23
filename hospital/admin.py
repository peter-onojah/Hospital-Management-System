from django.contrib import admin
from .models import Department, Doctor, Patient

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 20

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'department', 'specialization', 'is_available')
    list_filter = ('department', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'specialization', 'license_number')
    list_per_page = 20
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    get_full_name.short_description = 'Doctor'

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'blood_group', 'registration_date')
    list_filter = ('blood_group', 'registration_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('registration_date', 'last_updated')
    list_per_page = 20
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Patient Name'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user',)
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'allergies')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Registration Information', {
            'fields': ('registration_date', 'last_updated'),
            'classes': ('collapse',)
        }),
    )