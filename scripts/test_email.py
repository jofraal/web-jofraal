import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommercesite.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import logging

# Configure logging to see detailed error messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

# Get logger for SMTP connection
logger = logging.getLogger('django.core.mail')
logger.setLevel(logging.DEBUG)

def test_email_configuration():
    print("\nTesting email configuration...")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * 8} (hidden for security)")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Test recipient email - replace with your email for testing
    test_recipient = input("\nEnter your email address for testing: ")
    
    print(f"\nAttempting to send test email to {test_recipient}...")
    
    try:
        # Send a test email
        send_mail(
            subject='Test Email from Django Ecommerce Site',
            message='This is a test email to verify the email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_recipient],
            fail_silently=False,
        )
        print("\nEmail sent successfully! Please check your inbox (and spam folder).")
    except Exception as e:
        print(f"\nError sending email: {e}")
        print("\nPossible solutions:")
        print("1. Verify your Gmail app password is correct")
        print("2. Make sure 'Less secure app access' is enabled in your Google account")
        print("3. Check if you need to unlock your Google account for new device access")
        print("4. Verify there are no network/firewall issues blocking SMTP connections")

if __name__ == '__main__':
    test_email_configuration()
