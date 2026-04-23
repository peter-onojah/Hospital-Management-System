from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='home'),
    path('accounts/', include('accounts.urls')),
    path('hospital/', include('hospital.urls')),
    path('appointments/', include('appointments.urls')),
]