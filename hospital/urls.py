from django.urls import path
from . import views

urlpatterns = [
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('departments/', views.departments_list, name='departments_list'),
    path('api/doctors/', views.get_doctors_json, name='doctors_json'),
]
