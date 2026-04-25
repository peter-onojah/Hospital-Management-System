# accounts/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def format_action(action):
    """Format action string for display"""
    return action.replace('_', ' ').title()

@register.filter
def format_role(role):
    """Format role for display"""
    role_map = {
        'patient': 'Patient',
        'doctor': 'Doctor',
        'receptionist': 'Receptionist',
        'admin': 'Administrator',
    }
    return role_map.get(role, role.title())