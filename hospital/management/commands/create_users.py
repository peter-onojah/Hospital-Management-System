from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Create or update all required user accounts'
    
    def handle(self, *args, **kwargs):
        # Admin user
        admin, created = CustomUser.objects.get_or_create(
            username='Simon',
            defaults={
                'first_name': 'Simon',
                'last_name': 'Administrator',
                'email': 'admin@foundationhospital.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('bobby123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin: Simon/bobby123'))
        else:
            # Ensure admin has correct role and password
            admin.role = 'admin'
            admin.set_password('bobby123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Updated admin: Simon/bobby123'))
        
        # Receptionist
        receptionist, created = CustomUser.objects.get_or_create(
            username='receptionist',
            defaults={
                'first_name': 'Hospital',
                'last_name': 'Receptionist',
                'email': 'reception@foundationhospital.com',
                'role': 'receptionist',
            }
        )
        if created:
            receptionist.set_password('welcome123')
            receptionist.save()
            self.stdout.write(self.style.SUCCESS('Created receptionist: receptionist/welcome123'))
        else:
            receptionist.role = 'receptionist'
            receptionist.set_password('welcome123')
            receptionist.save()
            self.stdout.write(self.style.SUCCESS('Updated receptionist: receptionist/welcome123'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ All user accounts are ready!'))