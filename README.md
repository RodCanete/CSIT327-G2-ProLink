# ProLink

## 📖 Project Description
ProLink is a **web-based consultation and validation platform** that connects students and workers with professionals who can provide expert feedback, advice, and validation on academic or work-related outputs.  

The platform is designed to:  
- Improve work outcomes and boost user confidence  
- Provide affordable and credible access to experts  
- Create a transparent ecosystem where professionals can monetize their expertise  

---

## 🛠️ Tech Stack
- **Frontend:** HTML, CSS, JavaScript 
- **Backend:** Django 5.2.6 (Python)  
- **Database:** Supabase (PostgreSQL)  
- **Deployment:** Cloud-based hosting  

---

## 🚀 Core Features
- **User Registration & Authentication** – Secure sign-up and login system for professionals, students, and workers  
- **Professional Service Listings** – Professionals can list their services with customizable pricing options  
- **Secure Payment Processing** – Integrated gateways for safe and reliable transactions  
- **Rating & Review System** – Users can rate and review professionals to ensure credibility and transparency  
- **User & Transaction Dashboard** – Centralized dashboard for managing accounts, services, and payment history  

---

## ⚙️ Setup & Run Instructions

### Prerequisites
- Python 3.8 or higher
- Supabase account (for database)
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prolink
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Required packages:**
   ```
   asgiref==3.9.2
   Django==5.2.6
   sqlparse==0.5.3
   tzdata==2025.2
   ```

4. **Configure the database (Supabase)**
   - Create a free account at [Supabase](https://supabase.com/)
   - Create a new project
   - Navigate to Project Settings → Database
   - Copy your connection credentials
   - Create a `.env` file in the project root directory:
     ```env
     SUPABASE_URL=your_supabase_project_url
     SUPABASE_KEY=your_supabase_anon_key
     DB_NAME=postgres
     DB_USER=postgres
     DB_PASSWORD=your_supabase_db_password
     DB_HOST=your_supabase_host
     DB_PORT=5432
     ```
   - Install PostgreSQL adapter:
     ```bash
     pip install psycopg2-binary python-dotenv
     ```

5. **Update Django settings**
   - In `settings.py`, configure the database connection:
     ```python
     import os
     from dotenv import load_dotenv
     
     load_dotenv()
     
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': os.getenv('DB_NAME'),
             'USER': os.getenv('DB_USER'),
             'PASSWORD': os.getenv('DB_PASSWORD'),
             'HOST': os.getenv('DB_HOST'),
             'PORT': os.getenv('DB_PORT'),
         }
     }
     ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - **Frontend:** `http://localhost:8000`
   - **Admin Panel:** `http://localhost:8000/admin`

---

## 👥 Team Members

| Name | Role | CIT-U Email |
|------|------|-------------|
| Rod Gabrielle M. Cañete | Lead Developer | rodgabrielle.canete@cit.edu |
| Mac Howard T. Caranzo | Frontend Developer | machoward.caranzo@cit.edu |
| Patrick James A. Cantero | Backend Developer | patrickjames.cantero@cit.edu |

---

## 🌐 Deployed Link
**Live Application:** [Not yet deployed]

_Note: The deployment link will be updated once the application is hosted._

---

## 📄 License
This project is developed as part of an academic requirement.

---

## 📞 Contact
For questions or support, please contact any team member via their CIT-U email.
