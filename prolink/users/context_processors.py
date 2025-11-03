from django.contrib.auth import get_user_model
from .models import Profile

def profile_picture(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            return {'profile_picture_url': profile.profile_picture.url}
        except Profile.DoesNotExist:
            return {'profile_picture_url': None}
    return {'profile_picture_url': None}