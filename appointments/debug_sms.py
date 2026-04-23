import os
import django
import sys
import logging

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')
django.setup()

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from appointments.sms_service import KudiSMSService
from django.conf import settings

print("=" * 60)
print("DEBUG: KudiSMS Configuration Test")
print("=" * 60)

# Test 1: Check configuration
print("\n1. Checking SMS Configuration:")
print("-" * 40)

sms_service = KudiSMSService()
print(f"API Key configured: {bool(sms_service.api_key)}")
print(f"Sender ID: {sms_service.sender_id}")
print(f"API URL: {sms_service.api_url}")
print(f"Service enabled: {sms_service.enabled}")
print(f"Test Mode: {getattr(settings, 'SMS_TEST_MODE', 'Not set')}")

# Test 2: Test phone number formatting
print("\n2. Testing Phone Number Formatting:")
print("-" * 40)

test_numbers = ['08141544511', '2348141544511', '8141544511']
for number in test_numbers:
    formatted = sms_service.format_phone_number(number)
    print(f"{number} -> {formatted}")

# Test 3: Direct KudiSMS API Test
print("\n3. Testing KudiSMS API Directly:")
print("-" * 40)

import requests

# Your actual phone number for testing
TEST_PHONE = '08141544511'  # Use the number that's failing
TEST_MESSAGE = 'Debug test from Foundation Hospital'

# Format the phone
formatted_phone = sms_service.format_phone_number(TEST_PHONE)
print(f"Test phone: {TEST_PHONE}")
print(f"Formatted: {formatted_phone}")

# Prepare payload
payload = {
    'username': sms_service.api_key,
    'message': TEST_MESSAGE,
    'sender': sms_service.sender_id,
    'mobiles': formatted_phone,
    'dnd': 2
}

print(f"\nSending test to: {formatted_phone}")
print(f"Sender ID: {sms_service.sender_id}")
print(f"Message: {TEST_MESSAGE}")

try:
    # Make the request with verbose output
    print("\nMaking API request...")
    response = requests.post(
        sms_service.api_url, 
        data=payload, 
        timeout=30,
        headers={'User-Agent': 'Foundation-Hospital-Debug/1.0'}
    )
    
    print(f"\nResponse Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text[:500]}")
    
    # Try to parse JSON
    try:
        json_data = response.json()
        print(f"\nResponse JSON:")
        import json as json_module
        print(json_module.dumps(json_data, indent=2))
    except:
        print("\nCould not parse JSON response")
        
except Exception as e:
    print(f"\n❌ Exception during API call: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug test completed")
print("=" * 60)