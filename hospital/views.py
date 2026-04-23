from django.shortcuts import render
from .models import Department, Doctor
from django.http import JsonResponse

def doctors_list(request):
    """Display all doctors"""
    doctors = Doctor.objects.filter(is_available=True).select_related('user', 'department')
    departments = Department.objects.all()
    
    context = {
        'doctors': doctors,
        'departments': departments,
        'title': 'Our Doctors'
    }
    
    return render(request, 'hospital/doctors.html', context)

def departments_list(request):
    """Display all departments"""
    departments = Department.objects.all()
    
    context = {
        'departments': departments,
        'title': 'Our Departments'
    }
    
    return render(request, 'hospital/departments.html', context)

def get_doctors_json(request):
    """Return doctor data as JSON for the booking form"""
    doctors = Doctor.objects.filter(is_available=True).select_related('department', 'user')
    
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