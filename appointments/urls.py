# appointments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Patient URLs
    path('book/', views.book_appointment, name='book_appointment'),
    path('patient/', views.patient_appointments, name='patient_appointments'),
    path('patient/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    
    # Receptionist URLs
    path('receptionist/', views.receptionist_appointments, name='receptionist_appointments'),
    path('update-status/<uuid:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    path('sms-reminder/<uuid:appointment_id>/', views.schedule_sms_reminder, name='schedule_sms_reminder'),
    path('manual-sms/', views.manual_sms_sending, name='manual_sms_sending'),
    path('mark-sent/<int:reminder_id>/', views.mark_sms_as_sent, name='mark_sms_as_sent'),
    
    # SMS Status URLs
    path('sms-status/<uuid:appointment_id>/', views.sms_status_check, name='sms_status_check'),
    path('sms-dashboard/', views.sms_dashboard, name='sms_dashboard'),
    
    # API URLs
    path('api/sms-availability/', views.sms_availability_api, name='sms_availability_api'),
    path('api/sms-status/<uuid:appointment_id>/', views.sms_status_api, name='sms_status_api'),
    
    # Doctor URLs
    path('doctor/', views.doctor_appointments, name='doctor_appointments'),
    path('medical-history/<uuid:appointment_id>/', views.update_medical_history, name='update_medical_history'),
    
    # Test URLs
    path('test-sms/', views.test_sms_view, name='test_sms'),
    path('test-kudisms/', views.test_kudisms_api, name='test_kudisms_api'),
    path('api/check-sms-config/', views.check_sms_config_api, name='check_sms_config_api'),
    path('api/test-send-sms/', views.test_send_sms_api, name='test_send_sms_api'),
    path('sms-monitor/', views.sms_monitor, name='sms_monitor'),

]