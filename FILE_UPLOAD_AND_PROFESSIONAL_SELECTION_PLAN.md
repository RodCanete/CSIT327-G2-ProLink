# File Upload & Professional Selection Implementation Plan

## Current State Analysis

### Files Already Being Handled
Looking at `requests/views.py` lines 202-330, the system **already handles file uploads**:

1. ✅ Files are uploaded via `request.FILES.getlist('attached_files')`
2. ✅ Validation exists (max 5 files, 10MB each, specific file types)
3. ✅ Files are saved to `request_files/` directory with UUID names
4. ✅ File metadata stored as JSON in `Request.attached_files` field
5. ✅ Uses Django's `default_storage` system

### Database Schema
**Request Model** (`requests/models.py`):
```python
class Request(models.Model):
    # ... other fields ...
    attached_files = models.TextField(blank=True)  # JSON string
```

**File Metadata JSON Structure** (currently):
```json
[
  {
    "original_name": "document.pdf",
    "saved_name": "request_files/uuid-123.pdf",
    "size": 1024000
  }
]
```

---

## 📁 File Upload Implementation Plan

### Option 1: Keep Current System (RECOMMENDED for MVP)
**Status**: ✅ Already Working

**Pros**:
- Already implemented and functional
- Simple JSON storage
- Works with Django's file storage system
- Easy to migrate to Supabase Storage later

**Cons**:
- Files stored on local filesystem (won't work well on cloud hosting)
- No direct file management in database
- Harder to query file information

**Action Items**: None - it's working!

---

### Option 2: Create Dedicated File Model (Better Long-term)

**New Model** (`requests/models.py`):
```python
class RequestFile(models.Model):
    """Store file attachments for requests"""
    request = models.ForeignKey(
        Request, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    original_filename = models.CharField(max_length=255)
    saved_filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='request_files/')
    file_size = models.IntegerField()  # Size in bytes
    file_type = models.CharField(max_length=50)  # e.g., 'pdf', 'png'
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.EmailField()
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_filename} - {self.request.title}"
    
    def file_size_display(self):
        """Human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.2f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.2f} MB"
```

**Migration Strategy**:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Updated View** (`requests/views.py`):
```python
from .models import Request, RequestMessage, RequestFile

def create_request(request):
    # ... existing validation code ...
    
    # After creating Request object:
    request_obj = Request.objects.create(
        title=title,
        description=description,
        # ... other fields ...
    )
    
    # Handle file uploads with new model
    if 'attached_files' in request.FILES:
        files = request.FILES.getlist('attached_files')
        for file in files:
            # Validation
            if file.size > 10 * 1024 * 1024:
                continue
            
            # Create RequestFile record
            RequestFile.objects.create(
                request=request_obj,
                original_filename=file.name,
                saved_filename=f"{uuid.uuid4()}{os.path.splitext(file.name)[1]}",
                file_path=file,  # Django handles saving
                file_size=file.size,
                file_type=os.path.splitext(file.name)[1].lower()[1:],
                uploaded_by=user_email
            )
    
    return redirect('requests_list')
```

**Benefits**:
- ✅ Proper database relationships
- ✅ Easy to query files
- ✅ Can add file-level permissions
- ✅ Better for file management features
- ✅ Can track who uploaded each file

---

### Option 3: Supabase Storage Integration (Best for Production)

**Why Supabase Storage?**
- Already using Supabase for database
- CDN for fast file delivery
- Better for cloud deployment
- Built-in security policies
- Automatic backups

**Implementation**:

1. **Update `supabase_config.py`**:
```python
from supabase import create_client, Client

def get_storage_client():
    """Get Supabase storage client"""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return client.storage
```

2. **Create Storage Bucket** (one-time setup):
```python
# Run this once in Django shell or migration
storage = get_storage_client()
storage.create_bucket(
    'request-files',
    options={'public': False}  # Private by default
)
```

3. **Upload Helper Function**:
```python
def upload_file_to_supabase(file, request_id, user_email):
    """Upload file to Supabase Storage"""
    storage = get_storage_client()
    
    # Generate unique path
    file_extension = os.path.splitext(file.name)[1]
    unique_filename = f"{request_id}/{uuid.uuid4()}{file_extension}"
    
    # Upload to Supabase
    response = storage.from_('request-files').upload(
        path=unique_filename,
        file=file.read(),
        file_options={
            "content-type": file.content_type,
            "upsert": False
        }
    )
    
    # Get public URL (if bucket is public) or signed URL
    file_url = storage.from_('request-files').get_public_url(unique_filename)
    
    return {
        'original_name': file.name,
        'storage_path': unique_filename,
        'url': file_url,
        'size': file.size
    }
```

4. **Updated View**:
```python
def create_request(request):
    # ... validation ...
    
    attached_files = []
    if 'attached_files' in request.FILES:
        files = request.FILES.getlist('attached_files')
        for file in files:
            try:
                file_data = upload_file_to_supabase(file, request_obj.id, user_email)
                attached_files.append(file_data)
            except Exception as e:
                errors.append(f"Error uploading {file.name}: {str(e)}")
    
    request_obj.attached_files = json.dumps(attached_files)
    request_obj.save()
```

---

## 👨‍💼 Professional Selection Implementation Plan

### Current System
- Free-text field: User enters professional email manually
- No validation
- No dropdown/autocomplete
- No professional database

### Recommended Approach: Multi-Option System

#### Phase 1: Simple Selection (Immediate)

**Frontend Update** (`create_request.html`):
```html
<div class="form-group">
    <label for="professional" class="form-label">
        Preferred Professional (Optional)
    </label>
    <select id="professional_select" name="professional_select" class="form-select">
        <option value="">Auto-assign (Recommended)</option>
        <option value="manual">Enter specific professional email</option>
    </select>
    
    <!-- Manual email input (hidden by default) -->
    <div id="manual_professional_input" style="display: none; margin-top: 10px;">
        <input type="email" 
               id="professional" 
               name="professional" 
               class="form-input" 
               placeholder="Enter professional email">
    </div>
    
    <div class="form-help">
        Auto-assignment will match you with the best available professional based on your request.
    </div>
</div>

<script>
document.getElementById('professional_select').addEventListener('change', function(e) {
    const manualInput = document.getElementById('manual_professional_input');
    if (e.target.value === 'manual') {
        manualInput.style.display = 'block';
    } else {
        manualInput.style.display = 'none';
    }
});
</script>
```

---

#### Phase 2: Professional Database & Selection

**1. Query Active Professionals**:

**View Helper Function** (`requests/views.py`):
```python
from users.models import CustomUser, ProfessionalProfile

def get_available_professionals():
    """Get list of active professionals"""
    professionals = CustomUser.objects.filter(
        user_role='professional',
        is_active=True
    ).select_related('professionalprofile')
    
    return [{
        'email': prof.email,
        'name': f"{prof.first_name} {prof.last_name}",
        'specializations': [s.name for s in prof.professionalprofile.specializations.all()],
        'rating': prof.professionalprofile.average_rating,
        'hourly_rate': float(prof.professionalprofile.hourly_rate) if prof.professionalprofile.hourly_rate else None,
    } for prof in professionals if hasattr(prof, 'professionalprofile')]
```

**2. Updated Template** (`create_request.html`):
```html
<div class="form-group">
    <label for="professional" class="form-label">
        Select Professional (Optional)
    </label>
    
    <!-- Radio options -->
    <div class="selection-options" style="margin-bottom: 15px;">
        <label class="radio-option">
            <input type="radio" name="professional_option" value="auto" checked>
            <span>Auto-assign best match</span>
        </label>
        <label class="radio-option">
            <input type="radio" name="professional_option" value="select">
            <span>Select from list</span>
        </label>
        <label class="radio-option">
            <input type="radio" name="professional_option" value="manual">
            <span>Enter email manually</span>
        </label>
    </div>
    
    <!-- Professional selection dropdown -->
    <div id="professional_select_div" style="display: none;">
        <select id="professional_select" name="professional" class="form-select">
            <option value="">Choose a professional...</option>
            {% for prof in professionals %}
            <option value="{{ prof.email }}" 
                    data-rating="{{ prof.rating }}" 
                    data-rate="{{ prof.hourly_rate }}">
                {{ prof.name }} 
                {% if prof.specializations %}
                    ({{ prof.specializations|join:", " }})
                {% endif %}
                {% if prof.rating %}
                    ⭐ {{ prof.rating|floatformat:1 }}
                {% endif %}
            </option>
            {% endfor %}
        </select>
        
        <!-- Selected professional info card -->
        <div id="professional_info" style="display: none; margin-top: 10px; padding: 15px; background: var(--gray-50); border-radius: 8px;">
            <div class="professional-card">
                <h4 id="prof_name"></h4>
                <p id="prof_specializations"></p>
                <div style="display: flex; gap: 20px; margin-top: 10px;">
                    <span id="prof_rating"></span>
                    <span id="prof_rate"></span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Manual email input -->
    <div id="manual_email_div" style="display: none;">
        <input type="email" 
               id="professional_email" 
               name="professional_email" 
               class="form-input" 
               placeholder="professional@example.com">
    </div>
</div>

<style>
.radio-option {
    display: block;
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid var(--gray-200);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.radio-option:hover {
    background: var(--gray-50);
    border-color: var(--primary-color);
}

.radio-option input[type="radio"] {
    margin-right: 10px;
}

.professional-card h4 {
    margin: 0 0 8px 0;
    color: var(--gray-900);
}

.professional-card p {
    margin: 0;
    color: var(--gray-600);
    font-size: 14px;
}
</style>

<script>
document.querySelectorAll('input[name="professional_option"]').forEach(radio => {
    radio.addEventListener('change', function() {
        document.getElementById('professional_select_div').style.display = 'none';
        document.getElementById('manual_email_div').style.display = 'none';
        
        if (this.value === 'select') {
            document.getElementById('professional_select_div').style.display = 'block';
        } else if (this.value === 'manual') {
            document.getElementById('manual_email_div').style.display = 'block';
        }
    });
});

// Show professional info when selected
document.getElementById('professional_select').addEventListener('change', function(e) {
    const option = e.target.selectedOptions[0];
    const infoDiv = document.getElementById('professional_info');
    
    if (option.value) {
        document.getElementById('prof_name').textContent = option.text.split('(')[0].trim();
        document.getElementById('prof_specializations').textContent = 
            option.text.includes('(') ? option.text.match(/\((.*?)\)/)[1] : '';
        document.getElementById('prof_rating').textContent = 
            option.dataset.rating ? `⭐ ${option.dataset.rating}/5.0` : '';
        document.getElementById('prof_rate').textContent = 
            option.dataset.rate ? `$${option.dataset.rate}/hr` : '';
        infoDiv.style.display = 'block';
    } else {
        infoDiv.style.display = 'none';
    }
});
</script>
```

**3. Update View Context** (`requests/views.py`):
```python
def create_request(request):
    # ... existing code ...
    
    # GET request - show form
    context = {
        'user_email': user_email,
        'user_role': request.session.get('user_role', 'student'),
        'professionals': get_available_professionals(),  # Add this
    }
    return render(request, 'requests/create_request.html', context)
```

---

#### Phase 3: Smart Auto-Assignment Algorithm

**Matching Algorithm** (`requests/utils.py` - new file):
```python
from users.models import CustomUser, ProfessionalProfile
from requests.models import Request
from django.db.models import Avg, Count, Q

def auto_assign_professional(request_obj):
    """
    Intelligently assign a professional based on:
    - Availability
    - Specialization match
    - Rating
    - Workload
    - Past performance
    """
    
    # Get all active professionals
    professionals = CustomUser.objects.filter(
        user_role='professional',
        is_active=True
    ).select_related('professionalprofile').annotate(
        active_requests=Count(
            'requests',
            filter=Q(requests__status='in_progress')
        ),
        avg_rating=Avg('professionalprofile__reviews__rating')
    )
    
    # Score each professional
    scored_professionals = []
    for prof in professionals:
        score = 0
        
        # Availability (lower workload = higher score)
        if prof.active_requests < 3:
            score += 30
        elif prof.active_requests < 5:
            score += 20
        elif prof.active_requests < 8:
            score += 10
        
        # Rating (if available)
        if prof.avg_rating:
            score += (prof.avg_rating / 5.0) * 40  # Max 40 points
        else:
            score += 20  # Give new professionals a chance
        
        # Specialization match (if category provided)
        # TODO: Implement category matching
        
        # Response time (lower = better)
        # TODO: Track average response time
        
        scored_professionals.append((prof, score))
    
    # Sort by score (highest first)
    scored_professionals.sort(key=lambda x: x[1], reverse=True)
    
    # Return best match
    if scored_professionals:
        best_professional = scored_professionals[0][0]
        request_obj.professional = best_professional.email
        request_obj.save()
        return best_professional
    
    return None
```

**Use in View**:
```python
from .utils import auto_assign_professional

def create_request(request):
    # ... after creating request_obj ...
    
    # Handle professional assignment
    professional_option = request.POST.get('professional_option', 'auto')
    
    if professional_option == 'auto':
        # Auto-assign best match
        assigned_prof = auto_assign_professional(request_obj)
        if assigned_prof:
            messages.success(request, f"Request assigned to {assigned_prof.get_full_name()}")
    elif professional_option == 'select':
        # Use selected professional
        professional_email = request.POST.get('professional')
        if professional_email:
            request_obj.professional = professional_email
            request_obj.save()
    elif professional_option == 'manual':
        # Use manually entered email
        professional_email = request.POST.get('professional_email')
        if professional_email:
            # Validate professional exists
            if CustomUser.objects.filter(email=professional_email, user_role='professional').exists():
                request_obj.professional = professional_email
                request_obj.save()
            else:
                messages.warning(request, "Professional email not found. Request left unassigned.")
```

---

## 📋 Summary & Recommendations

### File Upload: Immediate Actions
1. ✅ **Keep current system** - it works!
2. 📅 **Phase 2** (optional): Create `RequestFile` model for better organization
3. 🚀 **Phase 3** (production): Migrate to Supabase Storage

### Professional Selection: Implementation Order
1. **Week 1**: Add simple select/auto/manual radio options
2. **Week 2**: Query professionals from database and populate dropdown
3. **Week 3**: Implement smart auto-assignment algorithm
4. **Week 4**: Add professional profiles view and rating system

### Priority Tasks
1. ✅ Files working - no action needed now
2. 🔴 Add professional selection UI (Phase 1)
3. 🟡 Create professional dropdown with data
4. 🟢 Implement auto-assignment logic

---

## 🎯 Next Steps

1. Choose professional selection approach
2. Update `create_request.html` template
3. Update `create_request` view
4. Test file uploads are still working
5. Test professional assignment flow

Let me know which approach you'd like to implement first!
