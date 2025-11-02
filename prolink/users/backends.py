from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using email
    instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            # User not found by email, return None
            return None
        
        # Check password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
