from django.core.management.base import BaseCommand
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Check if a user exists and show their details'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to check')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'✓ User found: {user.email}'))
            self.stdout.write(f'  - Username: {user.username}')
            self.stdout.write(f'  - Role: {user.user_role}')
            self.stdout.write(f'  - Active: {user.is_active}')
            self.stdout.write(f'  - Staff: {user.is_staff}')
            self.stdout.write(f'  - Created: {user.created_at}')
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ No user found with email: {email}'))
            self.stdout.write('\nTrying to find similar emails...')
            similar = CustomUser.objects.filter(email__icontains=email.split('@')[0])
            if similar.exists():
                for u in similar:
                    self.stdout.write(f'  - {u.email}')
            else:
                self.stdout.write('  No similar emails found')
