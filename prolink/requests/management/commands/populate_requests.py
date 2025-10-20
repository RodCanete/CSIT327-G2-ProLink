from django.core.management.base import BaseCommand
from requests.models import Request, RequestMessage
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populate the database with sample requests'

    def handle(self, *args, **options):
        # Clear existing data
        Request.objects.all().delete()
        
        # Create sample requests
        requests_data = [
            {
                'title': 'Research Paper Review',
                'description': 'Need expert review of my academic research paper on machine learning applications in healthcare. The paper is 15 pages and focuses on deep learning models for medical image analysis.',
                'client': 'student@university.edu',
                'professional': 'dr.sarah.johnson@expert.com',
                'status': 'in_progress',
                'price': 75.00,
                'timeline_days': 5,
                'created_at': datetime.now() - timedelta(days=2),
                'attached_files': '["research_paper.pdf", "references.docx"]'
            },
            {
                'title': 'Website Design Consultation',
                'description': 'Looking for professional feedback on my portfolio website design and user experience. Need help with responsive design and accessibility improvements.',
                'client': 'developer@portfolio.com',
                'professional': 'alex.rodriguez@design.com',
                'status': 'completed',
                'price': 120.00,
                'timeline_days': 3,
                'created_at': datetime.now() - timedelta(days=5),
                'completed_at': datetime.now() - timedelta(days=2),
                'attached_files': '["portfolio_screenshots.png", "wireframes.pdf"]'
            },
            {
                'title': 'Business Plan Review',
                'description': 'Need validation of my startup business plan before presenting to investors. Focus on financial projections and market analysis sections.',
                'client': 'entrepreneur@startup.com',
                'professional': '',
                'status': 'pending',
                'price': 200.00,
                'timeline_days': 7,
                'created_at': datetime.now() - timedelta(hours=6),
                'attached_files': '["business_plan.pdf", "financial_model.xlsx"]'
            },
            {
                'title': 'Code Review - React Application',
                'description': 'Need a senior developer to review my React application code for best practices, performance optimization, and security issues.',
                'client': 'developer@tech.com',
                'professional': 'maria.garcia@dev.com',
                'status': 'in_progress',
                'price': 150.00,
                'timeline_days': 4,
                'created_at': datetime.now() - timedelta(days=1),
                'attached_files': '["src_code.zip", "package.json"]'
            },
            {
                'title': 'Marketing Strategy Consultation',
                'description': 'Looking for expert advice on digital marketing strategy for my e-commerce business. Need help with SEO, social media, and paid advertising.',
                'client': 'business@ecommerce.com',
                'professional': 'marketing.expert@agency.com',
                'status': 'cancelled',
                'price': 300.00,
                'timeline_days': 10,
                'created_at': datetime.now() - timedelta(days=10),
                'attached_files': '["current_strategy.pdf", "analytics_report.pdf"]'
            }
        ]
        
        # Create requests
        for req_data in requests_data:
            request_obj = Request.objects.create(**req_data)
            self.stdout.write(f'Created request: {request_obj.title}')
            
            # Add some sample messages for in-progress requests
            if request_obj.status == 'in_progress':
                RequestMessage.objects.create(
                    request=request_obj,
                    sender_email=request_obj.client,
                    message="Hi! I've uploaded my work. Please let me know if you need any additional information.",
                    is_from_professional=False
                )
                
                RequestMessage.objects.create(
                    request=request_obj,
                    sender_email=request_obj.professional,
                    message="Thanks for the submission! I've started reviewing your work and will have feedback ready by tomorrow.",
                    is_from_professional=True
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample requests!')
        )
