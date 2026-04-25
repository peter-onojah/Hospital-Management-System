from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm  # Add this import
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


# Import CustomUser from accounts.models
from .models import CustomUser
from .forms import PatientRegistrationForm
from .forms import ReceptionistPatientRegistrationForm
from .forms import DoctorRegistrationForm
from .forms import AdminUserCreationForm, AdminUserEditForm
from django.shortcuts import get_object_or_404

# Import from other apps
from appointments.models import Appointment
from hospital.models import Doctor, Patient, Department


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Welcome message based on role
            # Check if user is superuser (admin)
            if user.is_superuser or user.role == 'admin':
                user.role = 'admin'  # Ensure role is set
                user.save()
                messages.success(request, f'Welcome Administrator, {user.username}!')
            elif user.role == 'doctor':
                messages.success(request, f'Welcome Dr. {user.last_name}!')
            elif user.role == 'receptionist':
                messages.success(request, f'Welcome Receptionist, {user.username}!')
            else:
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def patient_register(request):
    """Handle patient registration"""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Create patient profile
            Patient.objects.create(
                user=user,
                blood_group=form.cleaned_data.get('blood_group', ''),
                allergies=form.cleaned_data.get('allergies', ''),
                emergency_contact_name=form.cleaned_data.get('emergency_contact_name', ''),
                emergency_contact_phone=form.cleaned_data.get('emergency_contact_phone', '')
            )
            
            # Log the user in
            login(request, user)
            
            # Success message
            messages.success(request, 
                f'Registration successful! Welcome to Foundation Memorial Hospital, {user.first_name}.'
            )
            
            # Redirect to dashboard
            return redirect('dashboard')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    """Redirect users to their specific dashboard"""
    if request.user.role == 'patient':
        return redirect('patient_dashboard')
    elif request.user.role == 'doctor':
        return redirect('doctor_dashboard')
    elif request.user.role == 'receptionist':
        return redirect('receptionist_dashboard')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        return redirect('home')

@login_required
def patient_dashboard(request):
    """Patient dashboard view"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('home')
    
    # Get patient's appointments
    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor', 'doctor__user', 'department').order_by('-appointment_date')[:5]
    
    # Get upcoming appointments
    upcoming = Appointment.objects.filter(
        patient=patient,
        status='approved',
        appointment_date__gte=timezone.now().date()
    ).order_by('appointment_date', 'appointment_time')[:3]
    
    # Counts
    total_appointments = Appointment.objects.filter(patient=patient).count()
    pending_appointments = Appointment.objects.filter(patient=patient, status='pending').count()
    approved_appointments = Appointment.objects.filter(patient=patient, status='approved').count()
    
    context = {
        'appointments': appointments,
        'upcoming': upcoming,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'title': 'Patient Dashboard'
    }
    
    return render(request, 'dashboards/patient.html', context)

@login_required
def doctor_dashboard(request):
    """Doctor dashboard view"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        doctor = request.user.doctor_profile
    except:
        messages.error(request, 'Doctor profile not found.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status='approved'
    ).select_related('patient', 'patient__user').order_by('appointment_time')
    
    # Upcoming appointments (next 7 days)
    upcoming = Appointment.objects.filter(
        doctor=doctor,
        status='approved',
        appointment_date__gte=today,
        appointment_date__lte=today + timezone.timedelta(days=7)
    ).count()
    
    # Completed appointments this month
    this_month_start = timezone.now().replace(day=1)
    completed_this_month = Appointment.objects.filter(
        doctor=doctor,
        status='completed',
        appointment_date__gte=this_month_start
    ).count()
    
    # Patient statistics
    total_patients = Appointment.objects.filter(doctor=doctor).values('patient').distinct().count()
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_count': upcoming,
        'completed_this_month': completed_this_month,
        'total_patients': total_patients,
        'title': 'Doctor Dashboard'
    }
    
    return render(request, 'dashboards/doctor.html', context)

@login_required
def receptionist_dashboard(request):
    """Receptionist dashboard view"""
    if request.user.role != 'receptionist':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'patient__user', 'doctor', 'doctor__user').order_by('appointment_time')
    
    # Pending appointments
    pending_appointments = Appointment.objects.filter(
        status='pending'
    ).count()
    
    # Total appointments
    total_appointments = Appointment.objects.count()
    
    # Doctor availability
    available_doctors = Doctor.objects.filter(is_available=True).count()
    total_doctors = Doctor.objects.count()
    
    # Recent appointments (last 24 hours)
    yesterday = timezone.now() - timezone.timedelta(days=1)
    recent_appointments = Appointment.objects.filter(
        created_at__gte=yesterday
    ).select_related('patient', 'patient__user', 'doctor', 'doctor__user')[:5]
    
    context = {
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_appointments': total_appointments,
        'available_doctors': available_doctors,
        'total_doctors': total_doctors,
        'recent_appointments': recent_appointments,
        'title': 'Receptionist Dashboard'
    }
    
    return render(request, 'dashboards/receptionist.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # User statistics
    total_users = CustomUser.objects.count()
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_doctors = CustomUser.objects.filter(role='doctor').count()
    total_receptionists = CustomUser.objects.filter(role='receptionist').count()
    
    # Appointment statistics
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    
    # Department statistics
    departments = Department.objects.annotate(
        doctor_count=Count('doctor'),
        appointment_count=Count('appointment')
    )
    
    # Recent activity
    recent_appointments = Appointment.objects.select_related(
        'patient', 'patient__user', 'doctor', 'doctor__user'
    ).order_by('-created_at')[:5]
    
    # Recent registrations
    recent_patients = CustomUser.objects.filter(role='patient').order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_receptionists': total_receptionists,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
        'departments': departments,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
        'title': 'Admin Dashboard'
    }
    
    return render(request, 'dashboards/admin.html', context)

@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        # Handle profile updates
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'title': 'My Profile'})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep user logged in
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'title': 'Change Password'
    })


@login_required
def register_patient_by_receptionist(request):
    """Receptionist registers new patients"""
    if request.user.role != 'receptionist':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ReceptionistPatientRegistrationForm(request.POST)
        if form.is_valid():
            # Generate username
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.generate_username(first_name, last_name)
            
            # Generate or use custom password
            auto_generate = form.cleaned_data.get('auto_generate_password', True)
            custom_password = form.cleaned_data.get('custom_password', '')
            
            if auto_generate or not custom_password:
                password = form.generate_password()
            else:
                password = custom_password
            
            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                role='patient'
            )
            
            # Create patient profile
            Patient.objects.create(
                user=user,
                blood_group=form.cleaned_data.get('blood_group', ''),
                allergies=form.cleaned_data.get('allergies', ''),
                emergency_contact_name=form.cleaned_data.get('emergency_contact_name', ''),
                emergency_contact_phone=form.cleaned_data.get('emergency_contact_phone', '')
            )
            
            # Success message with credentials
            messages.success(request, 
                f'Patient registered successfully!<br>'
                f'<strong>Username:</strong> {username}<br>'
                f'<strong>Password:</strong> {password}<br><br>'
                f'Please provide these credentials to the patient.',
                extra_tags='safe'
            )
            return redirect('receptionist_dashboard')
    else:
        form = ReceptionistPatientRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Register New Patient'
    }
    return render(request, 'accounts/register_patient_receptionist.html', context)


@login_required
def add_doctor_by_admin(request):
    """Admin adds new doctors"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            # Generate username
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.generate_username(first_name, last_name)
            
            # Generate or use custom password
            auto_generate = form.cleaned_data.get('auto_generate_password', True)
            custom_password = form.cleaned_data.get('custom_password', '')
            
            if auto_generate or not custom_password:
                password = form.generate_password()
            else:
                password = custom_password
            
            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                role='doctor'
            )
            
            # Create doctor profile
            from hospital.models import Doctor
            Doctor.objects.create(
                user=user,
                department=form.cleaned_data['department'],
                qualification=form.cleaned_data['qualification'],
                specialization=form.cleaned_data['specialization'],
                license_number=form.cleaned_data['license_number'],
                experience=form.cleaned_data['experience'],
                consultation_fee=form.cleaned_data['consultation_fee'],
                available_days=form.cleaned_data['available_days'],
                available_time=form.cleaned_data['available_time'],
                is_available=form.cleaned_data['is_available'],
                bio=form.cleaned_data.get('bio', '')
            )
            
            # Success message with credentials
            messages.success(request, 
                f'Doctor registered successfully!<br>'
                f'<strong>Name:</strong> Dr. {first_name} {last_name}<br>'
                f'<strong>Username:</strong> {username}<br>'
                f'<strong>Password:</strong> {password}<br>'
                f'<strong>Specialization:</strong> {form.cleaned_data["specialization"]}<br>'
                f'<strong>Department:</strong> {form.cleaned_data["department"]}<br><br>'
                f'Please provide these credentials to the doctor.',
                extra_tags='safe'
            )
            return redirect('admin_dashboard')
    else:
        form = DoctorRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Add New Doctor'
    }
    return render(request, 'accounts/add_doctor.html', context)


@login_required
def user_management(request):
    """Admin manages all users"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Start with all users
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Apply filters
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Count by role
    total_users = users.count()
    patient_count = users.filter(role='patient').count()
    doctor_count = users.filter(role='doctor').count()
    receptionist_count = users.filter(role='receptionist').count()
    admin_count = users.filter(role='admin').count()
    active_count = users.filter(is_active=True).count()
    inactive_count = users.filter(is_active=False).count()
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_users': total_users,
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'receptionist_count': receptionist_count,
        'admin_count': admin_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'title': 'User Management'
    }
    
    return render(request, 'admin/user_management.html', context)

@login_required
def create_user(request):
    """Admin creates new users"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create profile based on role
            role = form.cleaned_data['role']
            if role == 'patient':
                Patient.objects.create(user=user)
            elif role == 'doctor':
                # Doctor profile will need additional fields
                pass
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_management')
    else:
        form = AdminUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Create New User'
    }
    return render(request, 'admin/create_user.html', context)

@login_required
def edit_user(request, user_id):
    """Admin edits user"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_management')
    else:
        form = AdminUserEditForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User: {user.username}'
    }
    return render(request, 'admin/edit_user.html', context)

@login_required
def toggle_user_status(request, user_id):
    """Activate/Deactivate user"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_management')
    
    user.is_active = not user.is_active
    user.save()
    
    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.username} {action} successfully!')
    
    return redirect('user_management')

@login_required
def reset_user_password(request, user_id):
    """Reset user password"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        import random
        import string
        
        # Generate random password
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(random.choice(characters) for _ in range(12))
        
        user.set_password(new_password)
        user.save()
        
        messages.success(request, 
            f'Password reset for {user.username}!<br>'
            f'<strong>New Password:</strong> {new_password}<br><br>'
            f'Please provide this password to the user.',
            extra_tags='safe'
        )
        return redirect('user_management')
    
    context = {
        'user': user,
        'title': f'Reset Password: {user.username}'
    }
    return render(request, 'admin/reset_password.html', context)


@login_required
def admin_reports(request):
    """Admin view system reports and analytics"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from django.db.models import Count, Sum, Avg, Q
    from datetime import datetime, timedelta
    from appointments.models import Appointment
    from hospital.models import Doctor, Department, Patient
    
    # Date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    # Get statistics
    total_appointments = Appointment.objects.count()
    appointments_today = Appointment.objects.filter(appointment_date=today).count()
    appointments_week = Appointment.objects.filter(appointment_date__gte=week_ago).count()
    appointments_month = Appointment.objects.filter(appointment_date__gte=month_ago).count()
    
    # Status distribution
    status_counts = Appointment.objects.values('status').annotate(count=Count('status'))
    status_data = {item['status']: item['count'] for item in status_counts}
    
    # Department statistics
    dept_stats = Department.objects.annotate(
        doctor_count=Count('doctor'),
        appointment_count=Count('appointment')
    )
    
    # Doctor statistics
    doctor_stats = Doctor.objects.annotate(
        appointment_count=Count('appointments'),
        completed_count=Count('appointments', filter=Q(appointments__status='completed'))
    ).order_by('-appointment_count')[:10]
    
    # Patient registration trends
    patient_registrations = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Patient.objects.filter(registration_date__date=date).count()
        patient_registrations.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Appointment trends (last 7 days)
    appointment_trends = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Appointment.objects.filter(appointment_date=date).count()
        appointment_trends.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Financial statistics (if we had payment data)
    total_consultation_fees = Doctor.objects.aggregate(
        total_fees=Sum('consultation_fee')
    )['total_fees'] or 0
    
    avg_consultation_fee = Doctor.objects.aggregate(
        avg_fee=Avg('consultation_fee')
    )['avg_fee'] or 0
    
    context = {
        'title': 'System Reports & Analytics',
        'today': today,
        'total_appointments': total_appointments,
        'appointments_today': appointments_today,
        'appointments_week': appointments_week,
        'appointments_month': appointments_month,
        'status_data': status_data,
        'dept_stats': dept_stats,
        'doctor_stats': doctor_stats,
        'patient_registrations': patient_registrations,
        'appointment_trends': appointment_trends,
        'total_consultation_fees': total_consultation_fees,
        'avg_consultation_fee': avg_consultation_fee,
    }
    
    return render(request, 'admin/reports.html', context)


@login_required
def admin_panel(request):
    """Main admin panel view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get statistics for dashboard
    from appointments.models import Appointment
    from hospital.models import Doctor
    
    total_users = CustomUser.objects.count()
    total_appointments = Appointment.objects.count()
    active_doctors = Doctor.objects.filter(is_available=True).count()
    pending_approvals = Appointment.objects.filter(status='pending').count()
    
    context = {
        'title': 'Admin Panel',
        'total_users': total_users,
        'total_appointments': total_appointments,
        'active_doctors': active_doctors,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'admin/admin_panel.html', context)

@login_required
def content_management(request):
    """Manage hospital content (departments, doctors, etc.)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from hospital.models import Department, Doctor
    
    departments = Department.objects.all()
    doctors = Doctor.objects.all().select_related('user', 'department')
    
    context = {
        'departments': departments,
        'doctors': doctors,
        'title': 'Content Management'
    }
    
    return render(request, 'admin/content_management.html', context)

@login_required
def system_settings(request):
    """System settings management"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    context = {
        'title': 'System Settings'
    }
    
    return render(request, 'admin/system_settings.html', context)

@login_required
def database_management(request):
    """Database backup and management"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    context = {
        'title': 'Database Management'
    }
    
    return render(request, 'admin/database_management.html', context)

@login_required
def audit_logs(request):
    """View system audit logs"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # In a real system, you would have an AuditLog model
    # For now, we'll use placeholder data
    logs = [
        {
            'timestamp': '2024-01-18 13:45:00',
            'user': 'admin',
            'action': 'LOGIN',
            'details': 'Admin logged in from IP 192.168.1.1',
            'ip_address': '192.168.1.1'
        },
        {
            'timestamp': '2024-01-18 13:30:00',
            'user': 'receptionist',
            'action': 'APPOINTMENT_APPROVED',
            'details': 'Approved appointment #A1B2C3D4',
            'ip_address': '192.168.1.2'
        },
        {
            'timestamp': '2024-01-18 13:15:00',
            'user': 'dr.john.doe',
            'action': 'MEDICAL_RECORD_UPDATE',
            'details': 'Updated medical record for patient #123',
            'ip_address': '192.168.1.3'
        },
    ]
    
    context = {
        'logs': logs,
        'title': 'Audit Logs'
    }
    
    return render(request, 'admin/audit_logs.html', context)


# Add this function in accounts/views.py (around line 450, after toggle_user_status function)
@login_required
def delete_user(request, user_id):
    """Admin deletes user account entirely"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_management')
    
    # Store username for message before deletion
    username = user.username
    full_name = user.get_full_name()
    
    # Delete the user (this will cascade delete related records)
    user.delete()
    
    messages.success(request, f'User "{full_name}" (username: {username}) has been permanently deleted.')
    return redirect('user_management')
    

    