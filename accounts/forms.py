from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class PatientRegistrationForm(UserCreationForm):
    # Personal Information
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text="Your legal first name"
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text="Your legal last name"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text="We'll send confirmation to this email"
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 08012345678'
        }),
        help_text="Your primary phone number"
    )
    
    # Contact Information
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your complete address'
        }),
        help_text="Your current residential address"
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Your date of birth"
    )
    
    # Medical Information
    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    
    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Your blood group (optional)"
    )
    
    allergies = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'List any known allergies (e.g., penicillin, peanuts)'
        }),
        help_text="Any known allergies (optional)"
    )
    
    # Emergency Contact
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name of emergency contact'
        }),
        help_text="Person to contact in case of emergency"
    )
    
    emergency_contact_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emergency contact phone number'
        }),
        help_text="Phone number of emergency contact"
    )
    
    # Username and Password (from UserCreationForm)
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        }),
        help_text="Choose a unique username for login"
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        }),
        help_text="Your password must contain at least 8 characters"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        help_text="Enter the same password as above for verification"
    )
    
    # Terms agreement
    terms_agreed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I agree to the terms and conditions",
        error_messages={'required': 'You must agree to the terms and conditions'}
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'phone', 'address', 'date_of_birth', 'password1', 'password2'
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Basic phone validation (can be enhanced)
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
        
        return user
    


# Add to accounts/forms.py
class ReceptionistPatientRegistrationForm(forms.ModelForm):
    """Form for receptionists to register patients"""
    # Personal Information
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'})
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter address'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Username will be auto-generated
    username = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # Medical Information
    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    allergies = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any allergies or leave blank if none'})
    )
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact name'})
    )
    emergency_contact_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact phone'})
    )
    
    # Password will be auto-generated
    auto_generate_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Auto-generate password"
    )
    
    custom_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter custom password (optional)'}),
        label="Or set custom password",
        help_text="Leave blank to auto-generate"
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth']
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        if email and CustomUser.objects.filter(email=email).exists():
            self.add_error('email', 'This email is already registered.')
        
        return cleaned_data
    
    def generate_username(self, first_name, last_name):
        """Generate a unique username from first and last name"""
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        username = base_username
        counter = 1
        
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def generate_password(self):
        """Generate a random password"""
        import random
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(12))
    

# Add to accounts/forms.py at the end
from hospital.models import Department  # Add this import at the top of the file

class DoctorRegistrationForm(forms.ModelForm):
    """Form for admins to register new doctors"""
    # User Information
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'})
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter address'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Professional Information (Doctor-specific)
    license_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter medical license number'})
    )
    specialization = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter specialization (e.g., Cardiologist)'})
    )
    qualification = forms.CharField(  # Note: singular as per your model
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter qualifications (e.g., MBBS, MD, etc.)'})
    )
    experience = forms.IntegerField(  # Note: 'experience' not 'years_of_experience' as per your model
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of experience'})
    )
    
    # Department
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    consultation_fee = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Consultation fee'})
    )
    
    # Availability
    available_days = forms.CharField(
        max_length=100,
        required=True,
        initial="Monday-Friday",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Monday-Friday'})
    )
    
    available_time = forms.CharField(
        max_length=100,
        required=True,
        initial="9:00 AM - 5:00 PM",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 9:00 AM - 5:00 PM'})
    )
    
    is_available = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Available for appointments"
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter doctor bio (optional)'})
    )
    
    # Account Information
    username = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    auto_generate_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Auto-generate password"
    )
    
    custom_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter custom password (optional)'}),
        label="Or set custom password",
        help_text="Leave blank to auto-generate"
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        from hospital.models import Doctor
        if Doctor.objects.filter(license_number=license_number).exists():
            raise forms.ValidationError("This license number is already registered.")
        return license_number
    
    def generate_username(self, first_name, last_name):
        """Generate a unique username from first and last name"""
        base_username = f"dr.{first_name.lower()}.{last_name.lower()}"
        username = base_username
        counter = 1
        
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def generate_password(self):
        """Generate a random password"""
        import random
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(12))
    

class AdminUserCreationForm(UserCreationForm):
    """Form for admin to create users"""
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('admin', 'Administrator'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 
                  'address', 'date_of_birth', 'role', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        
        return user

class AdminUserEditForm(forms.ModelForm):
    """Form for admin to edit users"""
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('admin', 'Administrator'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 
                  'address', 'date_of_birth', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }