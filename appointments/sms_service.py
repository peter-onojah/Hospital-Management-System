"""
SMS Service for KudiSMS Integration
Handles sending SMS reminders for appointments
"""

import requests
import json
import re
import logging
from django.conf import settings
from django.utils import timezone
from .models import SMSAppointmentReminder

# Set up logging
logger = logging.getLogger(__name__)

class KudiSMSService:
    """
    Service to handle SMS sending via KudiSMS API
    """
    
    def __init__(self):
        # Get SMS configuration from Django settings
        self.api_key = getattr(settings, 'KUDISMS_API_KEY', '')
        self.sender_id = getattr(settings, 'KUDISMS_SENDER_ID', 'FOUNDATION')
        
        # Correct API URL from documentation
        self.api_url = 'https://my.kudisms.net/api/sms'
        
        # Check if SMS is enabled
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            logger.info(f"SMS Service initialized with Sender ID: {self.sender_id}")
            logger.info(f"API URL: {self.api_url}")
        else:
            logger.warning("KudiSMS API key not configured. SMS sending disabled.")
    
    # Replace the clean_message_for_sms function in sms_service.py with:

    def clean_message_for_sms(self, message):
        """
        Simple message cleaning - just remove years and truncate
        """
        if not message:
            return "Appointment reminder from Foundation Hospital."
        
        # Simply remove any 4-digit years (2024-2030)
        import re
        message = re.sub(r'\b20[2-3][0-9]\b', '', message)
        
        # Clean up extra spaces
        message = ' '.join(message.split())
        
        # Ensure not empty
        if not message.strip():
            message = "Appointment reminder from Foundation Hospital."
        
        # Trim to 160 chars
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message.strip()


    def format_phone_number(self, phone_number):
        """
        Format Nigerian phone numbers for KudiSMS
        
        Args:
            phone_number (str): Raw phone number
            
        Returns:
            str: Formatted phone number or None if invalid
        """
        if not phone_number:
            return None
        
        # Remove all non-digits
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Handle Nigerian numbers
        if cleaned.startswith('0') and len(cleaned) == 11:
            # Convert 08012345678 to 2348012345678
            return '234' + cleaned[1:]
        elif cleaned.startswith('234') and len(cleaned) == 13:
            # Already in correct format
            return cleaned
        elif len(cleaned) == 10:
            # Handle numbers without leading 0
            return '234' + cleaned
        else:
            # Return as is (might be international)
            return cleaned
    
    def send_sms(self, phone_number, message, reminder_id=None):
        """
        Send SMS via KudiSMS API - WORKING IMPLEMENTATION
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'SMS service not configured',
                'message': 'KudiSMS API key not set'
            }
        
        # Format phone number for Nigeria
        formatted_number = self.format_phone_number(phone_number)
        if not formatted_number:
            return {
                'success': False,
                'error': 'Invalid phone number',
                'message': f'Invalid phone number: {phone_number}'
            }
        
        # Clean message to avoid spam filters
        cleaned_message = self.clean_message_for_sms(message)
        
        # Log if message was changed
        if cleaned_message != message:
            logger.info(f"Message cleaned. Original: {len(message)} chars, Cleaned: {len(cleaned_message)} chars")
            logger.info(f"Original: {message}")
            logger.info(f"Cleaned: {cleaned_message}")
        
        # Prepare JSON payload according to KudiSMS documentation
        json_payload = {
            'token': self.api_key,
            'senderID': self.sender_id,
            'recipients': formatted_number,
            'message': cleaned_message,
            'gateway': '2'  # 2 = Refunds charge for DND numbers
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            # REAL API CALL to KudiSMS - POST with JSON
            logger.info(f"Sending SMS to {formatted_number}")
            logger.info(f"Message: {cleaned_message[:50]}...")
            
            # Make API call with POST method and JSON body
            response = requests.post(
                self.api_url,
                json=json_payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Response Status Code: {response.status_code}")
            logger.info(f"Response Text: {response.text}")
            
            # Parse response
            success = False
            error_msg = "Unknown API response"
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Check for success indicators
                    if (response_data.get('status') == 'success' or 
                        response_data.get('error_code') == '000' or
                        'success' in str(response_data).lower()):
                        
                        success = True
                        error_msg = None
                        logger.info(f"SMS sent successfully! Cost: {response_data.get('cost', 'N/A')}, Balance: {response_data.get('balance', 'N/A')}")
                    else:
                        error_msg = response_data.get('msg', 'Unknown error from API')
                        logger.error(f"API Error: {error_msg}")
                        
                except ValueError:
                    # If not JSON, check text response
                    response_text = response.text.lower()
                    if ('sent' in response_text or 'success' in response_text):
                        success = True
                        error_msg = None
                    else:
                        error_msg = f'Unexpected response: {response.text}'
            else:
                error_msg = f'API returned status {response.status_code}: {response.text}'
                logger.error(f"HTTP Error: {error_msg}")
            
            # Prepare API response
            if success:
                api_response = {
                    'success': True,
                    'message': 'SMS sent successfully',
                    'recipient': formatted_number,
                    'raw_response': response.text,
                    'status_code': response.status_code
                }
            else:
                api_response = {
                    'success': False,
                    'error': error_msg,
                    'recipient': formatted_number,
                    'raw_response': response.text,
                    'status_code': response.status_code
                }
            
            # Update reminder status if reminder_id provided
            if reminder_id:
                if success:
                    self.update_reminder_status(reminder_id, 'sent', api_response)
                else:
                    self.update_reminder_status(reminder_id, 'failed', api_response)
            
            return api_response
            
        except requests.exceptions.Timeout:
            error_msg = "KudiSMS API timeout - check internet connection"
            logger.error(error_msg)
            
            if reminder_id:
                self.update_reminder_status(reminder_id, 'failed', {'error': 'API timeout'})
            
            return {
                'success': False,
                'error': 'API timeout',
                'message': 'Failed to connect to KudiSMS. Please check internet connection.'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to KudiSMS: {str(e)}"
            logger.error(error_msg)
            
            if reminder_id:
                self.update_reminder_status(reminder_id, 'failed', {'error': str(e)})
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Network error. Please check your internet connection.'
            }
            
        except Exception as e:
            error_msg = f"Error sending SMS: {str(e)}"
            logger.error(error_msg)
            
            if reminder_id:
                self.update_reminder_status(reminder_id, 'failed', {'error': str(e)})
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send SMS'
            }
    
    def update_reminder_status(self, reminder_id, status, api_response=None):
        """
        Update SMS reminder status in database
        
        Args:
            reminder_id (int): SMS reminder ID
            status (str): New status ('sent', 'failed')
            api_response (dict): API response data
        """
        try:
            reminder = SMSAppointmentReminder.objects.get(id=reminder_id)
            reminder.status = status
            
            if status == 'sent':
                reminder.sent_at = timezone.now()
            
            if api_response:
                reminder.api_response = str(api_response)[:500]  # Truncate if too long
            
            reminder.save()
            logger.info(f"Updated reminder {reminder_id} status to {status}")
            
        except SMSAppointmentReminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
        except Exception as e:
            logger.error(f"Error updating reminder {reminder_id}: {str(e)}")


def send_due_sms_reminders():
    """
    Check and send due SMS reminders - FIXED VERSION
    This function should be called by a scheduled task (cron/celery)
    """
    logger.info("=" * 50)
    logger.info("Starting SMS reminder check...")
    logger.info(f"Current time: {timezone.now()}")
    
    sms_service = KudiSMSService()
    
    # Check if SMS is enabled
    if not sms_service.enabled:
        logger.error("SMS service is not configured!")
        return []
    
    logger.info(f"SMS Service Enabled: {sms_service.enabled}")
    logger.info(f"Sender ID: {sms_service.sender_id}")
    
    # Get all scheduled reminders that are due (past their scheduled time)
    due_reminders = SMSAppointmentReminder.objects.filter(
        status__in=['scheduled', 'pending'],  # Check both statuses
        reminder_datetime__lte=timezone.now()
    ).select_related(
        'appointment', 
        'appointment__patient',
        'appointment__patient__user'
    ).order_by('reminder_datetime')
    
    logger.info(f"Found {due_reminders.count()} due reminders")
    
    if due_reminders.count() == 0:
        logger.info("No due reminders found.")
        return []
    
    results = []
    for reminder in due_reminders:
        try:
            logger.info("-" * 30)
            logger.info(f"Processing reminder ID: {reminder.id}")
            logger.info(f"Appointment ID: {reminder.appointment.appointment_id.hex[:8]}")
            logger.info(f"Patient: {reminder.appointment.patient.user.get_full_name()}")
            logger.info(f"Phone: {reminder.appointment.patient.user.phone}")
            logger.info(f"Original message: {reminder.message}")
            logger.info(f"Original message length: {len(reminder.message)}")
            
            # Get patient phone number
            phone_number = reminder.appointment.patient.user.phone
            
            if not phone_number:
                logger.error(f"No phone number for patient {reminder.appointment.patient.user.id}")
                reminder.status = 'failed'
                reminder.api_response = 'No phone number available'
                reminder.save()
                results.append({
                    'reminder_id': reminder.id,
                    'success': False,
                    'error': 'No phone number'
                })
                continue
            
            # Send SMS (message will be cleaned inside send_sms method)
            logger.info(f"Sending SMS to {phone_number}...")
            response = sms_service.send_sms(
                phone_number=phone_number,
                message=reminder.message,
                reminder_id=reminder.id
            )
            
            logger.info(f"SMS Response: {response}")
            
            results.append({
                'reminder_id': reminder.id,
                'appointment_id': reminder.appointment.appointment_id,
                'phone_number': phone_number,
                'success': response.get('success', False),
                'message': response.get('message', ''),
                'error': response.get('error', ''),
                'raw_response': response.get('raw_response', {})
            })
            
        except Exception as e:
            logger.error(f"Error processing reminder {reminder.id}: {str(e)}", exc_info=True)
            
            # Update reminder status to failed
            try:
                reminder.status = 'failed'
                reminder.api_response = f"Exception: {str(e)}"
                reminder.save()
            except:
                pass
            
            results.append({
                'reminder_id': reminder.id,
                'success': False,
                'error': str(e)
            })
    
    # Log summary
    success_count = sum(1 for r in results if r.get('success'))
    fail_count = len(results) - success_count
    
    logger.info("=" * 50)
    logger.info(f"SUMMARY: Processed {len(results)} reminders")
    logger.info(f"Success: {success_count}, Failed: {fail_count}")
    
    # Log each result
    for result in results:
        if result.get('success'):
            logger.info(f"✅ SUCCESS: {result.get('phone_number')}")
        else:
            logger.error(f"❌ FAILED: {result.get('phone_number')} - {result.get('error', 'No error message')}")
    
    return results


def test_sms_service():
    """
    Test function to verify SMS service is working
    """
    logger.info("Testing SMS service...")
    
    sms_service = KudiSMSService()
    
    if not sms_service.enabled:
        logger.warning("SMS service is not configured")
        return {
            'configured': False,
            'message': 'SMS service not configured. Please set KUDISMS_API_KEY in settings.'
        }
    
    # Test sending
    test_response = sms_service.send_sms(
        phone_number='08141544511',  # Your test number
        message='Test SMS from Foundation Hospital SMS Service',
        reminder_id=None
    )
    
    return {
        'configured': True,
        'test_response': test_response,
        'message': 'SMS service test completed'
    }