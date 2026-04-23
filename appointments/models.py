import uuid
from django.db import models
from django.conf import settings

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    appointment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    patient = models.ForeignKey(
        'hospital.Patient',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    doctor = models.ForeignKey(
        'hospital.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    department = models.ForeignKey(
        'hospital.Department',
        on_delete=models.CASCADE
    )
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Appointment {self.appointment_id.hex[:8]} - {self.patient} with Dr. {self.doctor.user.last_name}"
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
    
    def get_status_badge(self):
        status_colors = {
            'pending': 'warning',
            'approved': 'success',
            'completed': 'info',
            'cancelled': 'danger',
            'rescheduled': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')

class MedicalHistory(models.Model):
    patient = models.ForeignKey(
        'hospital.Patient',
        on_delete=models.CASCADE,
        related_name='medical_histories'
    )
    
    doctor = models.ForeignKey(
        'hospital.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record'
    )
    
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField()
    notes = models.TextField(blank=True)
    
    visit_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Medical History - {self.patient} - {self.visit_date}"
    
    class Meta:
        verbose_name_plural = "Medical Histories"
        ordering = ['-visit_date']

class SMSAppointmentReminder(models.Model):
    """Model to track SMS appointment reminders"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='sms_reminders'
    )
    
    reminder_datetime = models.DateTimeField(
        help_text="When the SMS should be sent"
    )
    
    message = models.TextField(
        help_text="SMS message content"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    api_response = models.TextField(
        blank=True,
        help_text="Response from SMS API"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"SMS Reminder for {self.appointment.appointment_id.hex[:8]}"
    
    class Meta:
        ordering = ['reminder_datetime']
        verbose_name = "SMS Appointment Reminder"
        verbose_name_plural = "SMS Appointment Reminders"
    
    def is_due(self):
        """Check if SMS should be sent now"""
        from django.utils import timezone
        return self.reminder_datetime <= timezone.now() and self.status == 'scheduled'
    