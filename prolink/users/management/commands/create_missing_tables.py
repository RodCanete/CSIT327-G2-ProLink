from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create missing tables that should exist based on migrations'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Creating missing tables ===')
        
        with connection.cursor() as cursor:
            # Create users_specialization table
            self.stdout.write('Creating users_specialization table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_specialization (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    icon VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ users_specialization table created'))
            
            # Create users_professionalprofile table
            self.stdout.write('Creating users_professionalprofile table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_professionalprofile (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL REFERENCES users_customuser(id) ON DELETE CASCADE,
                    experience_level VARCHAR(20) DEFAULT 'entry',
                    years_of_experience INTEGER DEFAULT 0,
                    certifications TEXT,
                    education TEXT,
                    languages VARCHAR(200),
                    hourly_rate NUMERIC(10, 2) DEFAULT 0,
                    consultation_fee NUMERIC(10, 2) DEFAULT 0,
                    is_available BOOLEAN DEFAULT TRUE,
                    timezone VARCHAR(50),
                    total_consultations INTEGER DEFAULT 0,
                    completed_consultations INTEGER DEFAULT 0,
                    average_rating NUMERIC(3, 2) DEFAULT 0.0,
                    total_reviews INTEGER DEFAULT 0,
                    portfolio_url VARCHAR(200),
                    linkedin_url VARCHAR(200),
                    website_url VARCHAR(200),
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    profile_views INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ users_professionalprofile table created'))
            
            # Create users_professionalprofile_specializations (many-to-many table)
            self.stdout.write('Creating users_professionalprofile_specializations table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_professionalprofile_specializations (
                    id BIGSERIAL PRIMARY KEY,
                    professionalprofile_id BIGINT NOT NULL REFERENCES users_professionalprofile(id) ON DELETE CASCADE,
                    specialization_id BIGINT NOT NULL REFERENCES users_specialization(id) ON DELETE CASCADE,
                    UNIQUE(professionalprofile_id, specialization_id)
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ users_professionalprofile_specializations table created'))
            
            # Create users_savedprofessional table
            self.stdout.write('Creating users_savedprofessional table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_savedprofessional (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users_customuser(id) ON DELETE CASCADE,
                    professional_id BIGINT NOT NULL REFERENCES users_professionalprofile(id) ON DELETE CASCADE,
                    notes TEXT,
                    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, professional_id)
                );
            """)
            self.stdout.write(self.style.SUCCESS('✓ users_savedprofessional table created'))
            
            # Create indexes for better performance
            self.stdout.write('Creating indexes...')
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_professional_user ON users_professionalprofile(user_id);
                CREATE INDEX IF NOT EXISTS idx_saved_user ON users_savedprofessional(user_id);
                CREATE INDEX IF NOT EXISTS idx_saved_professional ON users_savedprofessional(professional_id);
            """)
            self.stdout.write(self.style.SUCCESS('✓ Indexes created'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ All missing tables created successfully!'))
