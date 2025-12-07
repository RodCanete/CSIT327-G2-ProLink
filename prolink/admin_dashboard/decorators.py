from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator to ensure only admin users can access a view
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if request.user.user_role != 'admin':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

