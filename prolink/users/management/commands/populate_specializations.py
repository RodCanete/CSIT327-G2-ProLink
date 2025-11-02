from django.core.management.base import BaseCommand
from users.models import Specialization


class Command(BaseCommand):
    help = 'Populate the database with initial specialization categories'

    def handle(self, *args, **kwargs):
        specializations = [
            {
                'name': 'Software Development',
                'description': 'Software engineering, web development, mobile apps',
                'icon': 'fa-code'
            },
            {
                'name': 'Data Science',
                'description': 'Data analysis, machine learning, AI',
                'icon': 'fa-chart-line'
            },
            {
                'name': 'Graphic Design',
                'description': 'Logo design, branding, illustrations',
                'icon': 'fa-palette'
            },
            {
                'name': 'Content Writing',
                'description': 'Copywriting, blog posts, technical writing',
                'icon': 'fa-pen-fancy'
            },
            {
                'name': 'Digital Marketing',
                'description': 'SEO, social media, email marketing',
                'icon': 'fa-bullhorn'
            },
            {
                'name': 'Business Consulting',
                'description': 'Strategy, operations, management',
                'icon': 'fa-briefcase'
            },
            {
                'name': 'Legal Services',
                'description': 'Contract review, legal advice, compliance',
                'icon': 'fa-gavel'
            },
            {
                'name': 'Financial Planning',
                'description': 'Investment advice, budgeting, tax planning',
                'icon': 'fa-dollar-sign'
            },
            {
                'name': 'Education & Tutoring',
                'description': 'Academic tutoring, test prep, online courses',
                'icon': 'fa-graduation-cap'
            },
            {
                'name': 'Healthcare & Wellness',
                'description': 'Nutrition, fitness, mental health counseling',
                'icon': 'fa-heartbeat'
            },
            {
                'name': 'Architecture & Engineering',
                'description': 'Building design, structural engineering, CAD',
                'icon': 'fa-drafting-compass'
            },
            {
                'name': 'Photography & Video',
                'description': 'Photo editing, videography, animation',
                'icon': 'fa-camera'
            },
            {
                'name': 'Music & Audio',
                'description': 'Music production, audio editing, sound design',
                'icon': 'fa-music'
            },
            {
                'name': 'Translation & Languages',
                'description': 'Document translation, interpretation, localization',
                'icon': 'fa-language'
            },
            {
                'name': 'Real Estate',
                'description': 'Property consulting, market analysis, investment',
                'icon': 'fa-home'
            },
        ]

        created_count = 0
        updated_count = 0

        for spec_data in specializations:
            spec, created = Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults={
                    'description': spec_data['description'],
                    'icon': spec_data['icon'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {spec.name}')
                )
            else:
                # Update existing specialization
                spec.description = spec_data['description']
                spec.icon = spec_data['icon']
                spec.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated: {spec.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Complete! Created {created_count}, Updated {updated_count} specializations.'
            )
        )
