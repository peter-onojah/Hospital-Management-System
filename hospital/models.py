from django.db import models
from django.conf import settings

class Department(models.Model):
    """Hospital departments/services"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="fa-heartbeat")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Doctor(models.Model):
    """Doctor information linked to CustomUser"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    qualification = models.TextField()
    specialization = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    experience = models.IntegerField(help_text="Years of experience")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    available_days = models.CharField(max_length=100, default="Monday-Friday")
    available_time = models.CharField(max_length=100, default="9:00 AM - 5:00 PM")
    is_available = models.BooleanField(default=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"Dr. {self.user.last_name} {self.user.first_name}"
    
    class Meta:
        ordering = ['user__last_name']

class Patient(models.Model):
    """Patient information linked to CustomUser"""
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    blood_group = models.CharField(
        max_length=10, 
        choices=BLOOD_GROUP_CHOICES, 
        blank=True
    )
    allergies = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']