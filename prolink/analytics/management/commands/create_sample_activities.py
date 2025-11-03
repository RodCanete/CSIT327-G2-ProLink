"""
Management command to create sample data for testing the dashboard
Usage: python manage.py create_sample_activities <username>
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from analytics.models import ActivityLog
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Create sample activity logs for testing dashboard'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create activities for')
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of sample activities to create (default: 5)',
        )

    def handle(self, *args, **options):
        username = options['username']
        count = options['count']

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        # Sample activities
        sample_activities = [
            ('request_created', '<strong>Request created:</strong> "Website Redesign Project"'),
            ('request_in_progress', '<strong>Request in progress:</strong> "Logo Design" by Sarah Chen'),
            ('request_completed', '<strong>Validation completed:</strong> "Research Paper Review" by Dr. Alex Rodriguez'),
            ('review_given', '<strong>Left 5-star review</strong> for Maria Garcia'),
            ('professional_connected', '<strong>New professional match</strong> - John Smith (Web Developer)'),
        ]

        created_count = 0
        for i in range(count):
            activity_type, description = sample_activities[i % len(sample_activities)]
            
            # Create activity with timestamp slightly in the past
            created_at = timezone.now() - timedelta(hours=i * 2)
            
            activity = ActivityLog.objects.create(
                user=user,
                activity_type=activity_type,
                description=description,
                created_at=created_at
            )
            created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Created activity: {activity_type} - {created_at}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} sample activities for user "{username}"'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\nNote: Visit /dashboard/ to see the activities in action!'
            )
        )
