from flask import Blueprint

main = Blueprint('main', __name__)

# Import modules here to avoid circular dependencies until after main is defined
from . import views, errors
from ..models import Permission
from .. import photos


@main.app_context_processor
def inject_permissions():
    """Make Permissions available to template engine"""
    return dict(Permission=Permission, photos=photos)
