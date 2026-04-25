from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/patient/', views.patient_register, name='patient_register'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/receptionist/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Receptionist Patient Registration
    path('register/patient/receptionist/', views.register_patient_by_receptionist, name='register_patient_receptionist'),
    
    # Admin Doctor Management
    path('add/doctor/', views.add_doctor_by_admin, name='add_doctor_by_admin'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # accounts/urls.py - Add these to urlpatterns
    # User Management URLs
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/reset-password/<int:user_id>/', views.reset_user_password, name='reset_user_password'),

    path('reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin/content/', views.content_management, name='content_management'),
    path('admin/settings/', views.system_settings, name='system_settings'),
    path('admin/database/', views.database_management, name='database_management'),
    path('admin/logs/', views.audit_logs, name='audit_logs'),
]