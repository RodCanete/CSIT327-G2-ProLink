# Analytics App Documentation

## Overview
The `analytics` app provides real-time activity tracking, reviews, and dashboard metrics for the ProLink platform.

## Features Implemented

### 1. **Dynamic Dashboard Metrics**
- Active Requests Count (pending + in_progress)
- In Progress Requests
- Completed Validations
- Reviews Given with Average Rating
- Monthly Trends

### 2. **Real-Time Activity Logging**
Activities are automatically logged when:
- Request is created
- Request status changes (in progress, completed, cancelled)
- Review is given/received
- Professional is connected

### 3. **Reviews System**
- Clients can review professionals after request completion
- Professionals can review clients (hidden from clients, visible to other professionals)
- Reviews automatically update professional ratings
- Rating scale: 1-5 stars

### 4. **Recommended Professionals**
Based on:
- High ratings (minimum 4.0 stars)
- Availability status
- Number of reviews
- (Future: Related to user's past request categories)

### 5. **Active Requests Tracking**
- Shows progress percentage based on timeline
- Displays professional assigned
- Status badges (pending, in_progress, completed)

## Models

### Review
- `request`: ForeignKey to Request
- `reviewer`: User who wrote the review
- `reviewee`: User being reviewed
- `rating`: Integer (1-5)
- `comment`: TextField
- `is_professional_review`: Boolean
- `is_visible_to_client`: Boolean (auto-set based on reviewer type)

### ActivityLog
- `user`: User who performed the activity
- `activity_type`: Choice field
- `description`: HTML-safe description
- `request`: Optional ForeignKey
- `related_user`: Optional ForeignKey
- `review`: Optional ForeignKey
- `metadata`: JSONField for extra data
- `is_read`: Boolean

### Transaction (Placeholder)
- Ready for future payment integration
- Fields: amount, status, payment_method, transaction_id

## Signals

### Automatic Activity Logging
Located in `analytics/signals.py`:
- `log_request_activity`: Triggers on Request creation/update
- `log_review_activity`: Triggers on Review creation

## Utilities

Located in `analytics/utils.py`:
- `get_client_dashboard_metrics(user)`: Calculate all dashboard metrics
- `get_recent_activities(user, limit)`: Fetch recent activities
- `get_active_requests_tracking(user, limit)`: Get requests with progress
- `get_recommended_professionals(user, limit)`: Get top professionals
- `format_activity_for_display(activity)`: Format for template rendering
- `create_activity_log(...)`: Manual activity logging

## Usage in Views

```python
from analytics.utils import (
    get_client_dashboard_metrics,
    get_recent_activities,
    get_active_requests_tracking,
    get_recommended_professionals,
    format_activity_for_display
)

def dashboard(request):
    user = request.user
    
    # Get dashboard data
    metrics = get_client_dashboard_metrics(user)
    activities = get_recent_activities(user, limit=4)
    formatted_activities = [format_activity_for_display(a) for a in activities]
    active_requests_data = get_active_requests_tracking(user, limit=3)
    recommended_professionals = get_recommended_professionals(user, limit=3)
    
    context = {
        'metrics': metrics,
        'recent_activities': formatted_activities,
        'active_requests_tracking': active_requests_data,
        'recommended_professionals': recommended_professionals,
    }
    
    return render(request, 'dashboard_client.html', context)
```

## Template Usage

### Metrics
```django
{{ metrics.active_requests }}
{{ metrics.completed_validations }}
{{ metrics.reviews_given }}
{{ metrics.avg_rating_given }}
{{ metrics.trends.active_requests }}
```

### Activities
```django
{% for activity in recent_activities %}
    <div class="activity-icon {{ activity.color }}">
        <i class="{{ activity.icon }}"></i>
    </div>
    <p>{{ activity.description|safe }}</p>
    <span>{{ activity.time_ago }}</span>
{% endfor %}
```

### Active Requests
```django
{% for item in active_requests_tracking %}
    <h4>{{ item.request.title }}</h4>
    <p>{{ item.professional_name }}</p>
    <div style="width: {{ item.progress }}%"></div>
    <span>{{ item.status_display }}</span>
{% endfor %}
```

### Recommended Professionals
```django
{% for professional in recommended_professionals %}
    <h4>{{ professional.user.get_full_name }}</h4>
    <p>{{ professional.specializations.first.name }}</p>
    <span>{{ professional.average_rating|floatformat:1 }}</span>
{% endfor %}
```

## Future Enhancements

1. **Transaction System**
   - Integrate with payment gateway (Stripe/PayPal)
   - Track payments and earnings
   - Add "Total Spent" metric

2. **Advanced Recommendations**
   - ML-based matching
   - Category-based filtering
   - Past collaboration history

3. **Real-Time Notifications**
   - WebSocket integration
   - Push notifications
   - Email notifications

4. **Analytics Dashboard**
   - Charts and graphs
   - Time-series analysis
   - Export reports

## Testing

To test the analytics system:

1. **Create a Request**
   - Activity log should be created automatically
   - Dashboard metrics should update

2. **Update Request Status**
   - Change status to "in_progress" or "completed"
   - Check activity feed

3. **Create a Review**
   - After completing a request
   - Professional's rating should update
   - Activity log should be created

4. **Check Dashboard**
   - All metrics should show real data
   - Recent activities should display correctly
   - Recommended professionals should appear

## Admin Interface

Access at `/admin/analytics/`:
- View/edit Reviews
- Monitor ActivityLogs
- Manage Transactions (future)

All models are registered in `analytics/admin.py` with custom list displays and filters.
