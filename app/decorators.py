from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return function(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
