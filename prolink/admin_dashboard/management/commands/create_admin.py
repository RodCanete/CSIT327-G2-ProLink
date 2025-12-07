from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Create an admin user account'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Admin email address')
        parser.add_argument('--password', type=str, required=True, help='Admin password')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--username', type=str, default=None, help='Username (defaults to email)')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        username = options['username'] or email
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with email {email} already exists.'))
            return
        
        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username {username} already exists.'))
            return
        
        # Create admin user
        try:
            admin_user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_role='admin',
                is_admin=True,  # Set admin flag
                is_staff=True,  # Allow Django admin access
                is_superuser=False  # Not superuser by default
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Admin user created successfully!\n'
                f'   Email: {email}\n'
                f'   Username: {username}\n'
                f'   Role: Admin'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {str(e)}'))

