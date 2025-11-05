from django.contrib.auth import get_user_model

def profile_picture(request):
    """
    Context processor to make profile picture URL available in all templates
    """
    if request.user.is_authenticated:
        return {'profile_picture_url': request.user.profile_picture}
    return {'profile_picture_url': None}
