
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def administrator_required(view_function):
    """
    Allow superusers and members of the Administrator group.
    """

    @login_required
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):

        user = request.user

        is_administrator = (
            user.is_superuser
            or user.groups.filter(
                name="Administrator"
            ).exists()
        )

        if not is_administrator:
            raise PermissionDenied(
                "Administrator access is required."
            )

        return view_function(request, *args, **kwargs)

    return wrapper


def farm_worker_required(view_function):
    """
    Allow superusers, administrators, and farm staff.
    """

    @login_required
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):

        user = request.user

        allowed = (
            user.is_superuser
            or user.groups.filter(
                name__in=[
                    "Administrator",
                    "Farm Staff",
                ]
            ).exists()
        )

        if not allowed:
            raise PermissionDenied(
                "Farm staff access is required."
            )

        return view_function(request, *args, **kwargs)

    return wrapper
