from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def verified_user_required(view_func):
    """
    Decorator to ensure user is verified before accessing view
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Your profile is not set up. Please contact admin.')
            return redirect('dashboard')
        
        if request.user.profile.status != 'verified':
            messages.error(request, 'Your account is not verified. Please wait for admin approval.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_required(view_func):
    """
    Decorator to ensure user is admin/superuser
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper