from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Appointment, MedicalHistory
from .forms import AppointmentBookingForm, MedicalHistoryForm
from hospital.models import Doctor, Patient
from datetime import timedelta
from .forms import SMSReminderForm
from .models import Appointment, MedicalHistory, SMSAppointmentReminder
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@login_required
def book_appointment(request):
    """Patients can book appointments"""
    if request.user.role != 'patient':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('home')
    
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        print("=== DEBUG: Form submitted ===")
        print(f"POST data: {request.POST}")
        
        form = AppointmentBookingForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Non-field errors: {form.non_field_errors}")
            
        if form.is_valid():
            print("=== DEBUG: Form is valid, saving... ===")
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = 'pending'
            appointment.save()
            
            print(f"=== DEBUG: Appointment saved. ID: {appointment.appointment_id} ===")
            
            messages.success(request, 
                f'Appointment booked successfully! Your appointment ID is {appointment.appointment_id.hex[:8]}. '
                f'Status: Pending approval from reception.'
            )
            return redirect('patient_appointments')
        else:
            # Show form with errors
            messages.error(request, 'Please fix the errors below.')
    else:
        form = AppointmentBookingForm()
        print("=== DEBUG: Form created (GET request) ===")
    
    # Get available doctors for the template
    available_doctors = Doctor.objects.filter(is_available=True)
    
    context = {
        'form': form,
        'available_doctors': available_doctors,
        'title': 'Book Appointment'
    }
    return render(request, 'appointments/book.html', context)

@login_required
def patient_appointments(request):
    """View patient's appointments"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('home')
    
    appointments = Appointment.objects.filter(patient=patient).select_related(
        'doctor', 'doctor__user', 'department'
    ).order_by('-appointment_date', '-appointment_time')
    
    # Calculate counts
    total_appointments = appointments.count()
    pending_count = appointments.filter(status='pending').count()
    approved_count = appointments.filter(status='approved').count()
    completed_count = appointments.filter(status='completed').count()
    
    context = {
        'appointments': appointments,
        'total_appointments': total_appointments,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'title': 'My Appointments'
    }
    return render(request, 'appointments/patient_list.html', context)

@login_required
def patient_medical_history(request):
    """Patients can view their medical history"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('home')
    
    medical_history = MedicalHistory.objects.filter(
        patient=patient
    ).select_related('doctor', 'doctor__user', 'appointment').order_by('-visit_date')
    
    context = {
        'medical_history': medical_history,
        'title': 'My Medical History'
    }
    
    return render(request, 'appointments/patient_medical_history.html', context)

@login_required
def receptionist_appointments(request):
    """Receptionist views and manages all appointments with enhanced filters"""
    if request.user.role != 'receptionist':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    department_filter = request.GET.get('department', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Import models
    from hospital.models import Doctor, Department
    
    # Start with all appointments
    appointments = Appointment.objects.select_related(
        'patient', 'patient__user', 'doctor', 'doctor__user', 'department'
    ).order_by('-appointment_date', '-appointment_time')
    
    # Apply filters
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    
    if department_filter:
        appointments = appointments.filter(department_id=department_filter)
    
    # Apply date range filter
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Apply search filter
    if search_query:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(patient__user__phone__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query) |
            Q(symptoms__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    # Get all doctors and departments for filter dropdowns
    all_doctors = Doctor.objects.all().select_related('user')
    all_departments = Department.objects.all()
    
    # Counts for dashboard
    total = appointments.count()
    pending = appointments.filter(status='pending').count()
    approved = appointments.filter(status='approved').count()
    completed = appointments.filter(status='completed').count()
    cancelled = appointments.filter(status='cancelled').count()
    today = timezone.now().date()
    today_count = appointments.filter(appointment_date=today).count()
    
    # Get status distribution for chart
    status_counts = {
        'pending': pending,
        'approved': approved,
        'completed': completed,
        'cancelled': cancelled,
    }
    
    context = {
        'appointments': appointments,
        'all_doctors': all_doctors,
        'all_departments': all_departments,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'department_filter': department_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'total': total,
        'pending': pending,
        'approved': approved,
        'completed': completed,
        'cancelled': cancelled,
        'today_count': today_count,
        'status_counts': status_counts,
        'title': 'Manage Appointments'
    }
    return render(request, 'appointments/receptionist_list.html', context)

@login_required
def update_appointment_status(request, appointment_id):
    """Receptionist updates appointment status"""
    if request.user.role != 'receptionist':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Appointment.STATUS_CHOICES):
            old_status = appointment.status
            appointment.status = new_status
            appointment.notes = notes
            appointment.save()
            
            messages.success(request, 
                f'Appointment {appointment.appointment_id.hex[:8]} status updated from {old_status} to {new_status}.'
            )
            
            # NEW: If approving and patient has phone, redirect to SMS page
            if new_status == 'approved' and appointment.patient.user.phone:
                return redirect('schedule_sms_reminder', appointment_id=appointment.appointment_id)
    
    return redirect('receptionist_appointments')

@login_required
def doctor_appointments(request):
    """Doctor views their appointments"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        doctor = request.user.doctor_profile
    except:
        messages.error(request, 'Doctor profile not found.')
        return redirect('home')
    
    # Get today's date for filtering
    today = timezone.now().date()
    
    # Upcoming appointments
    upcoming = Appointment.objects.filter(
        doctor=doctor,
        status='approved',
        appointment_date__gte=today
    ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='approved',
        appointment_date=today
    ).select_related('patient', 'patient__user').order_by('appointment_time')
    
    # Past appointments
    past = Appointment.objects.filter(
        doctor=doctor,
        status='completed'
    ).select_related('patient', 'patient__user').order_by('-appointment_date', '-appointment_time')[:10]
    
    context = {
        'upcoming': upcoming,
        'today_appointments': today_appointments,
        'past': past,
        'title': 'My Appointments'
    }
    return render(request, 'appointments/doctor_list.html', context)

@login_required
def update_medical_history(request, appointment_id):
    """Doctor updates medical history after appointment"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    if appointment.doctor.user != request.user:
        messages.error(request, 'You can only update medical history for your own appointments.')
        return redirect('doctor_appointments')
    
    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            medical_history = form.save(commit=False)
            medical_history.patient = appointment.patient
            medical_history.doctor = appointment.doctor
            medical_history.appointment = appointment
            medical_history.save()
            
            
            # Mark appointment as completed
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, 'Medical history updated and appointment marked as completed.')
            return redirect('doctor_appointments')
    else:
        form = MedicalHistoryForm()
    
    context = {
        'form': form,
        'appointment': appointment,
        'title': 'Update Medical History'
    }
    return render(request, 'appointments/medical_history_form.html', context)

# Add to hospital/views.py
from django.http import JsonResponse

def get_doctors_json(request):
    """Return doctor data as JSON for the booking form"""
    doctors = Doctor.objects.filter(is_available=True).select_related('department')
    
    doctor_data = {}
    for doctor in doctors:
        doctor_data[str(doctor.id)] = {
            'name': f"{doctor.user.first_name} {doctor.user.last_name}",
            'department_id': doctor.department.id,
            'department_name': doctor.department.name,
            'consultation_fee': float(doctor.consultation_fee),
            'specialization': doctor.specialization
        }
    
    return JsonResponse(doctor_data)

@login_required
def schedule_sms_reminder(request, appointment_id):
    """Schedule SMS reminder for appointment"""
    if request.user.role != 'receptionist':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Check if appointment is approved
    if appointment.status != 'approved':
        messages.error(request, 'Can only schedule SMS reminders for approved appointments.')
        return redirect('receptionist_appointments')
    
    # Check if patient has phone number
    if not appointment.patient.user.phone:
        messages.error(request, 'Patient does not have a phone number registered. Cannot send SMS.')
        return redirect('receptionist_appointments')
    
    # Check if SMS already scheduled
    existing_reminder = SMSAppointmentReminder.objects.filter(
        appointment=appointment,
        status__in=['pending', 'scheduled']
    ).first()
    
    if existing_reminder:
        messages.info(request, f'SMS reminder already scheduled for {existing_reminder.reminder_datetime.strftime("%Y-%m-%d %I:%M %p")}.')
        return redirect('receptionist_appointments')
    
    if request.method == 'POST':
        form = SMSReminderForm(request.POST, appointment=appointment)
        if form.is_valid():
            sms_reminder = form.save()
            
            messages.success(request, 
                f'SMS reminder scheduled for {sms_reminder.reminder_datetime.strftime("%Y-%m-%d %I:%M %p")}. '
                f'Message: {sms_reminder.message[:50]}...'
            )
            return redirect('receptionist_appointments')
    else:
        form = SMSReminderForm(appointment=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'title': 'Schedule SMS Reminder'
    }
    return render(request, 'appointments/schedule_sms.html', context)


from .sms_service import test_sms_service  # Add this import

@login_required
def test_sms_view(request):
    """Test SMS service (admin only)"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        # Test sending an SMS
        from .sms_service import KudiSMSService
        sms_service = KudiSMSService()
        
        test_phone = request.POST.get('test_phone', '')
        test_message = request.POST.get('test_message', 'Test SMS from Foundation Hospital')
        
        if test_phone:
            result = sms_service.send_sms(test_phone, test_message)
            messages.info(request, f"SMS Test Result: {result.get('message', 'No response')}")
        else:
            messages.error(request, 'Please enter a test phone number')
    
    # Run basic test
    test_results = test_sms_service()
    
    context = {
        'test_results': test_results,
        'title': 'Test SMS Service'
    }
    
    return render(request, 'appointments/test_sms.html', context)


@login_required
def sms_status_check(request, appointment_id):
    """Check SMS status for an appointment (AJAX endpoint)"""
    if request.user.role not in ['receptionist', 'admin']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Get the latest SMS reminder for this appointment
    sms_reminder = SMSAppointmentReminder.objects.filter(
        appointment=appointment
    ).order_by('-created_at').first()
    
    if sms_reminder:
        response_data = {
            'has_reminder': True,
            'reminder_id': sms_reminder.id,
            'status': sms_reminder.status,
            'reminder_time': sms_reminder.reminder_datetime.strftime("%Y-%m-%d %I:%M %p"),
            'message_preview': sms_reminder.message[:50] + '...' if len(sms_reminder.message) > 50 else sms_reminder.message,
            'sent_at': sms_reminder.sent_at.strftime("%Y-%m-%d %I:%M %p") if sms_reminder.sent_at else None,
        }
    else:
        response_data = {
            'has_reminder': False,
            'message': 'No SMS reminder scheduled'
        }
    
    return JsonResponse(response_data)

@login_required
def sms_dashboard(request):
    """SMS Dashboard for monitoring"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get SMS statistics
    total_sms = SMSAppointmentReminder.objects.count()
    sent_sms = SMSAppointmentReminder.objects.filter(status='sent').count()
    scheduled_sms = SMSAppointmentReminder.objects.filter(status='scheduled').count()
    failed_sms = SMSAppointmentReminder.objects.filter(status='failed').count()
    
    # Daily SMS count for last 7 days
    daily_counts = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = SMSAppointmentReminder.objects.filter(
            created_at__date=date
        ).count()
        daily_counts.append({
            'date': date.strftime('%a'),
            'count': count
        })
    
    # Recent SMS activity
    recent_sms = SMSAppointmentReminder.objects.select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user',
        'appointment__doctor',
        'appointment__doctor__user'
    ).order_by('-created_at')[:10]
    
    # Upcoming SMS reminders (next 24 hours)
    next_24_hours = timezone.now() + timedelta(hours=24)
    upcoming_reminders = SMSAppointmentReminder.objects.filter(
        status='scheduled',
        reminder_datetime__gte=timezone.now(),
        reminder_datetime__lte=next_24_hours
    ).select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user'
    ).order_by('reminder_datetime')
    
    context = {
        'title': 'SMS Dashboard',
        'total_sms': total_sms,
        'sent_sms': sent_sms,
        'scheduled_sms': scheduled_sms,
        'failed_sms': failed_sms,
        'daily_counts': daily_counts,
        'recent_sms': recent_sms,
        'upcoming_reminders': upcoming_reminders,
        'today': today,
    }
    
    return render(request, 'appointments/sms_dashboard.html', context)

@login_required
def test_kudisms_api(request):
    """Test KudiSMS API integration"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from .sms_service import KudiSMSService, test_sms_service
    
    test_results = {
        'config': {},
        'test_send': None,
        'balance': None
    }
    
    # Check configuration
    sms_service = KudiSMSService()
    test_results['config'] = {
        'api_key_configured': bool(sms_service.api_key),
        'sender_id': sms_service.sender_id,
        'api_url': sms_service.api_url,
        'enabled': sms_service.enabled,
        'test_mode': getattr(settings, 'SMS_TEST_MODE', False)
    }
    
    if request.method == 'POST':
        # Send test SMS
        test_phone = request.POST.get('test_phone', '').strip()
        test_message = request.POST.get('test_message', 'Test SMS from Foundation Hospital SMS Service').strip()
        
        if test_phone:
            # Send real test SMS
            result = sms_service.send_sms(test_phone, test_message)
            test_results['test_send'] = result
            
            if result.get('success'):
                messages.success(request, f"✓ Test SMS sent successfully to {test_phone}")
                # Try to get balance
                if 'balance' in result:
                    test_results['balance'] = result['balance']
            else:
                messages.error(request, f"✗ Failed to send test SMS: {result.get('error', 'Unknown error')}")
        else:
            messages.error(request, 'Please enter a phone number for testing.')
    
    # Run basic service test
    service_test = test_sms_service()
    test_results['service_test'] = service_test
    
    context = {
        'test_results': test_results,
        'title': 'Test KudiSMS API'
    }
    
    return render(request, 'appointments/test_kudisms.html', context)


@login_required
def manual_sms_sending(request):
    """Manual SMS sending interface for failed/upcoming SMS"""
    if request.user.role not in ['receptionist', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from datetime import datetime, timedelta
    
    # Get SMS that need manual sending
    now = timezone.now()
    
    # Failed SMS
    failed_sms = SMSAppointmentReminder.objects.filter(
        status='failed'
    ).select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user',
        'appointment__doctor'
    ).order_by('-reminder_datetime')[:20]
    
    # Upcoming SMS (next 24 hours)
    next_24h = now + timedelta(hours=24)
    upcoming_sms = SMSAppointmentReminder.objects.filter(
        status='scheduled',
        reminder_datetime__lte=next_24h
    ).select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user',
        'appointment__doctor'
    ).order_by('reminder_datetime')
    
    # Sent SMS (last 24 hours)
    last_24h = now - timedelta(hours=24)
    sent_sms = SMSAppointmentReminder.objects.filter(
        status='sent',
        sent_at__gte=last_24h
    ).select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user'
    ).order_by('-sent_at')[:10]
    
    context = {
        'title': 'Manual SMS Sending',
        'failed_sms': failed_sms,
        'upcoming_sms': upcoming_sms,
        'sent_sms': sent_sms,
        'now': now,
        'kudisms_url': 'https://account.kudisms.net/send',
    }
    
    return render(request, 'appointments/manual_sms.html', context)

@login_required
def mark_sms_as_sent(request, reminder_id):
    """Manually mark SMS as sent"""
    if request.user.role not in ['receptionist', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    reminder = get_object_or_404(SMSAppointmentReminder, id=reminder_id)
    
    if request.method == 'POST':
        reminder.status = 'sent'
        reminder.sent_at = timezone.now()
        reminder.api_response = 'Manually marked as sent via web interface'
        reminder.save()
        
        messages.success(request, f'SMS marked as sent for {reminder.appointment.patient.user.get_full_name()}')
        return redirect('manual_sms_sending')
    
    return redirect('manual_sms_sending')


@csrf_exempt  # Allow AJAX calls without CSRF for this endpoint
def sms_availability_api(request):
    """API endpoint to check if SMS features are available"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check SMS configuration
    api_key_configured = bool(getattr(settings, 'KUDISMS_API_KEY', ''))
    test_mode = getattr(settings, 'SMS_TEST_MODE', True)
    simulation_mode = getattr(settings, 'SMS_SIMULATION', True)
    
    # Determine if SMS is "available" (either real or simulation)
    if api_key_configured and not test_mode and not simulation_mode:
        available = True
        mode = 'production'
    elif simulation_mode or test_mode:
        available = True  # Available in simulation mode
        mode = 'simulation'
    else:
        available = False
        mode = 'disabled'
    
    response_data = {
        'available': available,
        'mode': mode,
        'api_configured': api_key_configured,
        'test_mode': test_mode,
        'simulation_mode': simulation_mode,
        'sender_id': getattr(settings, 'KUDISMS_SENDER_ID', 'Not set'),
    }
    
    return JsonResponse(response_data)

@csrf_exempt
def sms_status_api(request, appointment_id):
    """API endpoint to get SMS status for an appointment"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .models import Appointment, SMSAppointmentReminder
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        
        # Get the latest SMS reminder
        sms_reminder = SMSAppointmentReminder.objects.filter(
            appointment=appointment
        ).order_by('-created_at').first()
        
        if sms_reminder:
            response_data = {
                'has_reminder': True,
                'reminder_id': sms_reminder.id,
                'status': sms_reminder.status,
                'reminder_time': sms_reminder.reminder_datetime.strftime("%Y-%m-%d %I:%M %p"),
                'sent_at': sms_reminder.sent_at.strftime("%Y-%m-%d %I:%M %p") if sms_reminder.sent_at else None,
                'message_preview': sms_reminder.message[:50] + '...' if len(sms_reminder.message) > 50 else sms_reminder.message,
            }
        else:
            response_data = {
                'has_reminder': False,
                'message': 'No SMS reminder scheduled'
            }
        
        return JsonResponse(response_data)
        
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def check_sms_config_api(request):
    """Check SMS configuration (for test page)"""
    from .sms_service import KudiSMSService
    
    sms_service = KudiSMSService()
    
    response_data = {
        'configured': sms_service.enabled,
        'test_mode': getattr(settings, 'SMS_TEST_MODE', True),
        'sender_id': sms_service.sender_id,
        'has_api_key': bool(sms_service.api_key),
    }
    
    return JsonResponse(response_data)

@csrf_exempt
def test_send_sms_api(request):
    """Test sending SMS via API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        phone = data.get('phone', '')
        message = data.get('message', '')
        
        if not phone or not message:
            return JsonResponse({'success': False, 'error': 'Phone and message required'})
        
        from .sms_service import KudiSMSService
        sms_service = KudiSMSService()
        
        result = sms_service.send_sms(phone, message)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@login_required
def sms_monitor(request):
    """Monitor SMS system status"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # SMS statistics
    total_sms = SMSAppointmentReminder.objects.count()
    today = timezone.now().date()
    
    stats = {
        'total': total_sms,
        'sent': SMSAppointmentReminder.objects.filter(status='sent').count(),
        'scheduled': SMSAppointmentReminder.objects.filter(status='scheduled').count(),
        'failed': SMSAppointmentReminder.objects.filter(status='failed').count(),
        'pending': SMSAppointmentReminder.objects.filter(status='pending').count(),
        'today': SMSAppointmentReminder.objects.filter(
            created_at__date=today
        ).count(),
        'last_24h': SMSAppointmentReminder.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count(),
    }
    
    # Recent activity
    recent_sms = SMSAppointmentReminder.objects.select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user'
    ).order_by('-created_at')[:10]
    
    # Due reminders
    due_reminders = SMSAppointmentReminder.objects.filter(
        status='scheduled',
        reminder_datetime__lte=timezone.now()
    ).count()
    
    # Test API connection
    from .sms_service import KudiSMSService
    sms_service = KudiSMSService()
    api_status = {
        'configured': sms_service.enabled,
        'sender_id': sms_service.sender_id,
        'test_mode': getattr(settings, 'SMS_TEST_MODE', False),
    }
    
    context = {
        'title': 'SMS System Monitor',
        'stats': stats,
        'recent_sms': recent_sms,
        'due_reminders': due_reminders,
        'api_status': api_status,
        'current_time': timezone.now(),
    }
    
    return render(request, 'appointments/sms_monitor.html', context)

