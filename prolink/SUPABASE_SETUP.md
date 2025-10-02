# 🚀 Supabase Authentication Setup Guide for ProLink

## **Prerequisites**
- Django project running
- Python virtual environment activated
- Supabase account (free tier available)

## **Step 1: Create Supabase Project**

### 1.1 Sign Up for Supabase
1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up with GitHub, Google, or email
4. Verify your email if required

### 1.2 Create New Project
1. Click **"New Project"**
2. Fill in project details:
   - **Name**: `prolink-auth`
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is sufficient for development
3. Click **"Create new project"**
4. Wait 2-3 minutes for project setup

## **Step 2: Get Supabase Credentials**

### 2.1 Access Project Settings
1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these credentials:
   - **Project URL**: `https://your-project-id.supabase.co`
   - **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 2.2 Update Configuration
1. Open `prolink/supabase_config.py`
2. Replace the placeholder values with your actual credentials:
   ```python
   SUPABASE_URL = "https://your-actual-project-id.supabase.co"
   SUPABASE_ANON_KEY = "your-actual-anon-key"
   SUPABASE_SERVICE_ROLE_KEY = "your-actual-service-role-key"
   ```

## **Step 3: Configure Authentication Settings**

### 3.1 Enable Email Authentication
1. In Supabase dashboard, go to **Authentication** → **Settings**
2. Under **Auth Providers**, ensure **Email** is enabled
3. Configure **Site URL**: `http://localhost:8000` (for development)
4. Add **Redirect URLs**: `http://localhost:8000/dashboard/`

### 3.2 Configure Email Templates (Optional)
1. Go to **Authentication** → **Email Templates**
2. Customize the confirmation and reset password emails
3. Set **Enable email confirmations** to `false` for development (optional)

## **Step 4: Test the Setup**

### 4.1 Start Django Server
```bash
cd prolink
..\env\Scripts\Activate.ps1
python manage.py runserver
```

### 4.2 Test Registration
1. Go to `http://localhost:8000/signup/`
2. Fill out the registration form
3. Check if user is created in Supabase dashboard under **Authentication** → **Users**

### 4.3 Test Login
1. Go to `http://localhost:8000/login/`
2. Use the email and password from registration
3. Verify you're redirected to dashboard

### 4.4 Test Logout
1. From dashboard, click on user menu → Logout
2. Verify you're redirected to landing page

## **Step 5: Database Schema (Optional)**

### 5.1 Create User Profiles Table
If you want to store additional user data, create a table in Supabase:

1. Go to **Table Editor** in Supabase dashboard
2. Click **"New Table"**
3. Create table named `user_profiles`:
   ```sql
   CREATE TABLE user_profiles (
     id UUID REFERENCES auth.users(id) PRIMARY KEY,
     first_name TEXT,
     last_name TEXT,
     role TEXT CHECK (role IN ('student', 'worker', 'professional')),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

### 5.2 Enable Row Level Security (RLS)
1. Go to **Authentication** → **Policies**
2. Create policies for the `user_profiles` table
3. Enable RLS on the table

## **Step 6: Production Configuration**

### 6.1 Environment Variables
For production, use environment variables instead of the config file:

```python
# In settings.py
import os
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
```

### 6.2 Security Settings
1. Update **Site URL** to your production domain
2. Update **Redirect URLs** to your production URLs
3. Enable **Email confirmations** for production
4. Set up proper CORS settings

## **Troubleshooting**

### Common Issues:

1. **"Invalid API key" error**
   - Check that you've copied the correct keys from Supabase dashboard
   - Ensure there are no extra spaces in the configuration

2. **"User not found" error**
   - Check if email confirmation is required
   - Verify the user exists in Supabase dashboard

3. **CORS errors**
   - Add your domain to allowed origins in Supabase settings
   - Check that your site URL is correctly configured

4. **Session not persisting**
   - Ensure Django sessions are properly configured
   - Check that cookies are being set correctly

### Debug Mode:
Add this to your views for debugging:
```python
import logging
logger = logging.getLogger(__name__)

# In your auth views
logger.info(f"Supabase response: {response}")
```

## **Next Steps**

1. **User Profiles**: Create a user profile system to store additional data
2. **Role-based Access**: Implement different dashboards based on user roles
3. **Email Verification**: Enable email confirmation for production
4. **Password Reset**: Implement password reset functionality
5. **Social Login**: Add Google/GitHub authentication options

## **Files Modified**

- `prolink/supabase_config.py` - Supabase configuration
- `prolink/prolink/settings.py` - Django settings updated
- `prolink/users/views.py` - Authentication views updated
- `prolink/users/urls.py` - Added logout URL
- `prolink/templates/users/login.html` - Updated for email login
- `prolink/templates/users/signup.html` - Removed username field
- `prolink/templates/dashboard.html` - Added logout functionality

## **Dependencies Added**

- `supabase` - Supabase Python client
- `python-dotenv` - Environment variable management

---

**🎉 Congratulations!** Your ProLink application now has Supabase authentication integrated!
