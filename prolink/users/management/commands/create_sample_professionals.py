from django.core.management.base import BaseCommand
from users.models import CustomUser, ProfessionalProfile, Specialization
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample professional accounts for testing'

    def handle(self, *args, **kwargs):
        professionals_data = [
            {
                'username': 'drsmith',
                'email': 'sarah.smith@example.com',
                'password': 'testpass123',
                'first_name': 'Sarah',
                'last_name': 'Smith',
                'bio': 'Experienced software developer with 10+ years in full-stack development. Specializing in Python, Django, React, and cloud architecture.',
                'profile': {
                    'experience_level': 'expert',
                    'years_of_experience': 12,
                    'hourly_rate': Decimal('150.00'),
                    'consultation_fee': Decimal('75.00'),
                    'certifications': 'AWS Certified Solutions Architect\nPMP Certified\nGoogle Cloud Professional',
                    'education': 'BS Computer Science - MIT\nMS Software Engineering - Stanford',
                    'languages': 'English, Spanish',
                    'average_rating': Decimal('4.9'),
                    'total_reviews': 45,
                    'completed_consultations': 120,
                    'total_consultations': 125,
                    'is_verified': True,
                    'specializations': ['Software Development', 'Data Science']
                }
            },
            {
                'username': 'jdoe',
                'email': 'john.doe@example.com',
                'password': 'testpass123',
                'first_name': 'John',
                'last_name': 'Doe',
                'bio': 'Creative graphic designer with a passion for branding and visual storytelling. 8 years of agency experience.',
                'profile': {
                    'experience_level': 'experienced',
                    'years_of_experience': 8,
                    'hourly_rate': Decimal('85.00'),
                    'consultation_fee': Decimal('50.00'),
                    'certifications': 'Adobe Certified Expert\nBrand Strategy Certificate',
                    'education': 'BFA Graphic Design - Rhode Island School of Design',
                    'languages': 'English',
                    'average_rating': Decimal('4.8'),
                    'total_reviews': 32,
                    'completed_consultations': 95,
                    'total_consultations': 98,
                    'is_verified': True,
                    'specializations': ['Graphic Design']
                }
            },
            {
                'username': 'mjohnson',
                'email': 'maria.johnson@example.com',
                'password': 'testpass123',
                'first_name': 'Maria',
                'last_name': 'Johnson',
                'bio': 'Digital marketing strategist helping businesses grow through SEO, content marketing, and social media campaigns.',
                'profile': {
                    'experience_level': 'intermediate',
                    'years_of_experience': 5,
                    'hourly_rate': Decimal('95.00'),
                    'consultation_fee': Decimal('60.00'),
                    'certifications': 'Google Analytics Certified\nHubSpot Inbound Marketing\nFacebook Blueprint',
                    'education': 'BA Marketing - University of California, Berkeley',
                    'languages': 'English, Portuguese',
                    'average_rating': Decimal('4.7'),
                    'total_reviews': 28,
                    'completed_consultations': 67,
                    'total_consultations': 70,
                    'is_verified': True,
                    'is_available': True,
                    'specializations': ['Digital Marketing', 'Content Writing']
                }
            },
            {
                'username': 'dlee',
                'email': 'david.lee@example.com',
                'password': 'testpass123',
                'first_name': 'David',
                'last_name': 'Lee',
                'bio': 'Business consultant specializing in startup strategy, operations optimization, and market analysis.',
                'profile': {
                    'experience_level': 'expert',
                    'years_of_experience': 15,
                    'hourly_rate': Decimal('200.00'),
                    'consultation_fee': Decimal('100.00'),
                    'certifications': 'MBA - Harvard Business School\nCertified Management Consultant',
                    'education': 'MBA - Harvard Business School\nBS Economics - Yale University',
                    'languages': 'English, Mandarin, Korean',
                    'average_rating': Decimal('5.0'),
                    'total_reviews': 18,
                    'completed_consultations': 54,
                    'total_consultations': 54,
                    'is_verified': True,
                    'is_featured': True,
                    'specializations': ['Business Consulting']
                }
            },
            {
                'username': 'awilliams',
                'email': 'amanda.williams@example.com',
                'password': 'testpass123',
                'first_name': 'Amanda',
                'last_name': 'Williams',
                'bio': 'Licensed attorney with expertise in contract law, business formations, and intellectual property protection.',
                'profile': {
                    'experience_level': 'experienced',
                    'years_of_experience': 9,
                    'hourly_rate': Decimal('250.00'),
                    'consultation_fee': Decimal('150.00'),
                    'certifications': 'Licensed Attorney - State Bar of California\nIntellectual Property Specialist',
                    'education': 'JD - Columbia Law School\nBA Political Science - Georgetown University',
                    'languages': 'English, French',
                    'average_rating': Decimal('4.9'),
                    'total_reviews': 22,
                    'completed_consultations': 78,
                    'total_consultations': 80,
                    'is_verified': True,
                    'specializations': ['Legal Services']
                }
            },
        ]

        created_count = 0
        skipped_count = 0

        for prof_data in professionals_data:
            # Check if user already exists
            if CustomUser.objects.filter(username=prof_data['username']).exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠ Skipped: {prof_data['username']} (already exists)")
                )
                skipped_count += 1
                continue

            # Create user
            user = CustomUser.objects.create_user(
                username=prof_data['username'],
                email=prof_data['email'],
                password=prof_data['password'],
                first_name=prof_data['first_name'],
                last_name=prof_data['last_name'],
                user_role='professional',
                bio=prof_data['bio']
            )

            # Extract specialization names
            spec_names = prof_data['profile'].pop('specializations')

            # Create professional profile
            profile = ProfessionalProfile.objects.create(
                user=user,
                **prof_data['profile']
            )

            # Add specializations
            for spec_name in spec_names:
                try:
                    spec = Specialization.objects.get(name=spec_name)
                    profile.specializations.add(spec)
                except Specialization.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Specialization '{spec_name}' not found")
                    )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created: {user.get_full_name()} (@{user.username})")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Complete! Created {created_count}, Skipped {skipped_count} professionals.'
            )
        )
