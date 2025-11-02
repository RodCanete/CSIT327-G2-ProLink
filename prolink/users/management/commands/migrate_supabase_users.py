from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import ProfessionalProfile, Specialization
import json

CustomUser = get_user_model()


class Command(BaseCommand):
    help = 'Migrate users from Supabase Auth to Django CustomUser model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            help='Path to JSON file containing exported Supabase users',
        )
        parser.add_argument(
            '--default-password',
            type=str,
            default='TempPassword123!',
            help='Default password for migrated users (they should reset it)',
        )

    def handle(self, *args, **options):
        json_file = options.get('json_file')
        default_password = options['default_password']

        if not json_file:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  No JSON file provided. Manual user migration process:\n\n'
                    '1. Export users from Supabase:\n'
                    '   - Go to Supabase Dashboard > Authentication > Users\n'
                    '   - Export user data to JSON\n\n'
                    '2. Run this command with --json-file:\n'
                    '   python manage.py migrate_supabase_users --json-file path/to/users.json\n\n'
                    '3. Or create users manually in Django admin:\n'
                    '   python manage.py createsuperuser\n\n'
                    'For now, you can test with newly created Django users.\n'
                )
            )
            return

        # Load Supabase users from JSON
        try:
            with open(json_file, 'r') as f:
                supabase_users = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File not found: {json_file}'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'❌ Invalid JSON file: {json_file}'))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for supabase_user in supabase_users:
            email = supabase_user.get('email')
            if not email:
                skipped_count += 1
                continue

            # Get user metadata
            user_metadata = supabase_user.get('user_metadata', {})
            first_name = user_metadata.get('first_name', '')
            last_name = user_metadata.get('last_name', '')
            role = user_metadata.get('role', 'client')

            # Check if user already exists
            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️  User already exists: {email}')
                )
                skipped_count += 1
                continue

            try:
                # Create Django user
                user = CustomUser.objects.create_user(
                    username=email,
                    email=email,
                    password=default_password,
                    first_name=first_name,
                    last_name=last_name,
                    user_role=role
                )

                # Build bio from metadata
                bio_parts = []
                if role == "professional":
                    profession = user_metadata.get('profession', '')
                    experience = user_metadata.get('experience', '')
                    if profession:
                        bio_parts.append(f"Professional in {profession}")
                    if experience:
                        bio_parts.append(f"{experience} level experience")
                elif role == "student":
                    school = user_metadata.get('school_name', '')
                    major = user_metadata.get('major', '')
                    if school:
                        bio_parts.append(f"Student at {school}")
                    if major:
                        bio_parts.append(f"Major: {major}")
                elif role == "worker":
                    job_title = user_metadata.get('job_title', '')
                    company = user_metadata.get('company_name', '')
                    if job_title:
                        bio_parts.append(job_title)
                    if company:
                        bio_parts.append(f"at {company}")

                if bio_parts:
                    user.bio = " | ".join(bio_parts)
                    user.save()

                # Create professional profile if needed
                if role == "professional":
                    experience = user_metadata.get('experience', 'entry')
                    profile = ProfessionalProfile.objects.create(
                        user=user,
                        experience_level=experience,
                        years_of_experience=0,
                        hourly_rate=50.00,
                        is_available=True
                    )

                    # Try to add specialization
                    profession = user_metadata.get('profession', '')
                    if profession:
                        try:
                            specialization = Specialization.objects.get(name__iexact=profession)
                            profile.specializations.add(specialization)
                        except Specialization.DoesNotExist:
                            pass

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created user: {email} ({role})')
                )
                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create {email}: {str(e)}')
                )
                skipped_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Migration Complete!'))
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Skipped: {skipped_count}')
        self.stdout.write('\n⚠️  Important: All migrated users have the default password:')
        self.stdout.write(f'   "{default_password}"')
        self.stdout.write('   Users should reset their passwords on first login.\n')
