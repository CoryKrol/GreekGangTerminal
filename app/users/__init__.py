from flask import Blueprint

users = Blueprint('users', __name__)

from . import views
from ..models import Permission
from .. import photos


@users.app_context_processor
def inject_permissions():
    """Make Permissions available to template engine"""
    return dict(Permission=Permission, photos=photos)
