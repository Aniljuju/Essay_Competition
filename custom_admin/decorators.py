from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Restricts view to staff or superuser accounts only.
    Usage:
        @login_required
        @admin_required
        def my_view(request): ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access the admin panel.")
        return redirect('login')
    return wrapper
