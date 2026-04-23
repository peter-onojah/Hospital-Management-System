from django import forms
from django.utils import timezone
from .models import Appointment, MedicalHistory, SMSAppointmentReminder
from hospital.models import Doctor, Department
from datetime import datetime, timedelta
import pytz
import json

class AppointmentBookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show available doctors
        self.fields['doctor'].queryset = Doctor.objects.filter(is_available=True)
        
        # Set minimum date to tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.fields['appointment_date'].widget.attrs['min'] = tomorrow
        
        # Add ID to doctor field for JavaScript
        self.fields['doctor'].widget.attrs.update({
            'class': 'form-select',
            'id': 'id_doctor_select'
        })
        
        # Make department field read-only and add ID
        self.fields['department'].widget.attrs.update({
            'class': 'form-select',
            'id': 'id_department_select',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa;'
        })
        
        # Prepare doctor data for template
        self.doctor_data = {}
        doctors = Doctor.objects.filter(is_available=True).select_related('department', 'user')
        for doctor in doctors:
            self.doctor_data[str(doctor.id)] = {
                'department_id': str(doctor.department.id),
                'consultation_fee': float(doctor.consultation_fee),
                'name': f"Dr. {doctor.user.get_full_name()}",
                'specialization': doctor.specialization,
                'department_name': doctor.department.name
            }
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'department', 'appointment_date', 'appointment_time', 'symptoms']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'appointment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'appointment_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your symptoms in detail...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        if doctor and appointment_date and appointment_time:
            # Check if doctor already has appointment at that time
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).exists()
            
            if existing:
                raise forms.ValidationError(
                    "This doctor already has an appointment at the selected time. Please choose a different time."
                )
            
            # Check if date is in the past
            if appointment_date < timezone.now().date():
                raise forms.ValidationError("Appointment date cannot be in the past.")
            
            # Check if it's too far in future (max 3 months)
            max_date = timezone.now().date() + timedelta(days=90)
            if appointment_date > max_date:
                raise forms.ValidationError("Appointments can only be booked up to 3 months in advance.")
        
        return cleaned_data
    
    @property
    def doctor_data_json(self):
        """Return doctor data as JSON string for JavaScript"""
        return json.dumps(self.doctor_data)

class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ['diagnosis', 'treatment', 'prescription', 'notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter diagnosis...'
            }),
            'treatment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe treatment provided...'
            }),
            'prescription': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter prescription details...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
        }

class SMSReminderForm(forms.ModelForm):
    """Form for scheduling SMS reminders with custom time options"""
    
    REMINDER_TIME_CHOICES = [
        ('custom', 'Set custom date & time'),
        ('1', '1 hour before appointment'),
        ('2', '2 hours before appointment'),
        ('3', '3 hours before appointment'),
        ('6', '6 hours before appointment'),
        ('12', '12 hours before appointment'),
        ('24', '1 day before appointment'),
        ('48', '2 days before appointment'),
        ('72', '3 days before appointment'),
    ]
    
    reminder_option = forms.ChoiceField(
        choices=REMINDER_TIME_CHOICES,
        initial='24',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'reminder_option'
        }),
        help_text="Choose when to send the reminder"
    )
    
    custom_datetime = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'id': 'custom_datetime'
        }),
        help_text="Select specific date and time for the reminder"
    )
    
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Customize the SMS message or leave blank for default message...'
        }),
        help_text="Optional: Customize the SMS message (max 160 characters)"
    )
    
    class Meta:
        model = SMSAppointmentReminder
        fields = []
    
    def __init__(self, *args, **kwargs):
        self.appointment = kwargs.pop('appointment', None)
        super().__init__(*args, **kwargs)
        
        if self.appointment:
            # Set initial message based on appointment
            self.fields['custom_message'].initial = self.generate_default_message()
            
            # Set min datetime for custom_datetime (now + 5 minutes)
            min_datetime = timezone.now() + timedelta(minutes=5)
            min_datetime_str = min_datetime.strftime('%Y-%m-%dT%H:%M')
            self.fields['custom_datetime'].widget.attrs['min'] = min_datetime_str
            
            # Set max datetime (appointment time - 5 minutes)
            appointment_datetime = self.get_appointment_datetime()
            max_datetime = appointment_datetime - timedelta(minutes=5)
            max_datetime_str = max_datetime.strftime('%Y-%m-%dT%H:%M')
            self.fields['custom_datetime'].widget.attrs['max'] = max_datetime_str
    
    def get_appointment_datetime(self):
        """Convert appointment date and time to timezone-aware datetime"""
        if not self.appointment:
            return None
        
        appointment_datetime = datetime.combine(
            self.appointment.appointment_date,
            self.appointment.appointment_time
        )
        
        # Convert to timezone-aware datetime
        tz = pytz.timezone('Africa/Lagos')
        return tz.localize(appointment_datetime)
    
    def generate_default_message(self):
        """Generate shorter default SMS message (under 160 chars) WITHOUT FUTURE YEARS"""
        if not self.appointment:
            return ""
        
        patient = self.appointment.patient.user.first_name
        doctor = self.appointment.doctor.user.last_name
        department = self.appointment.department.name
        
        # Shorten department name if needed
        if len(department) > 20:
            department = department[:17] + "..."
        
        # Use date without year to avoid spam filters
        date = self.appointment.appointment_date.strftime("%d %b")  # "05 Feb" format
        time = self.appointment.appointment_time.strftime("%I:%M%p").lstrip('0')  # "3:30PM" format
        
        # Create message WITHOUT year
        message = f"Dear {patient}, your {department} appt with Dr {doctor} at {time} on {date} is confirmed. FDN Hospital."
        
        # If still too long, make it even shorter
        if len(message) > 160:
            message = f"Dear {patient}, your appt at {time} on {date} is confirmed. FDN Hospital."
        
        # Final check and truncate if needed
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message
    
    def clean_custom_message(self):
        """Validate custom message length"""
        custom_message = self.cleaned_data.get('custom_message', '').strip()
        
        if custom_message and len(custom_message) > 160:
            raise forms.ValidationError(
                f"SMS messages must be 160 characters or less. "
                f"Current length: {len(custom_message)} characters."
            )
        
        return custom_message
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.appointment:
            raise forms.ValidationError("Appointment is required.")
        
        appointment_datetime = self.get_appointment_datetime()
        reminder_option = cleaned_data.get('reminder_option')
        custom_datetime = cleaned_data.get('custom_datetime')
        custom_message = cleaned_data.get('custom_message', '')
        
        # Calculate reminder time based on option
        if reminder_option == 'custom':
            if not custom_datetime:
                raise forms.ValidationError("Please select a custom date and time for the reminder.")
            
            # Ensure custom datetime is in the future
            if custom_datetime < timezone.now():
                raise forms.ValidationError("Reminder time cannot be in the past.")
            
            # Ensure custom datetime is before appointment
            if custom_datetime >= appointment_datetime:
                raise forms.ValidationError("Reminder time must be before the appointment time.")
            
            reminder_datetime = custom_datetime
            
        else:
            # Calculate based on hours before appointment
            hours_before = int(reminder_option)
            reminder_datetime = appointment_datetime - timedelta(hours=hours_before)
            
            # Ensure reminder is not in the past
            if reminder_datetime < timezone.now():
                raise forms.ValidationError(
                    f"Cannot schedule reminder {hours_before} hours before - it would be in the past. "
                    f"Please choose a later reminder time."
                )
        
        # Use custom message or generate default
        if custom_message:
            message = custom_message
            # ENSURE it's not too long (should already be validated)
            if len(message) > 160:
                message = message[:157] + "..."
        else:
            message = self.generate_default_message()
        
        # FINAL LENGTH CHECK
        if len(message) > 160:
            # This should never happen with above checks, but just in case
            message = message[:157] + "..."
        
        cleaned_data['reminder_datetime'] = reminder_datetime
        cleaned_data['message'] = message
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save SMS reminder"""
        sms_reminder = SMSAppointmentReminder(
            appointment=self.appointment,
            reminder_datetime=self.cleaned_data['reminder_datetime'],
            message=self.cleaned_data['message'],
            status='scheduled'
        )
        
        if commit:
            sms_reminder.save()
        
        return sms_reminder