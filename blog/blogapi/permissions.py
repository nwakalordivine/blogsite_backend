from rest_framework.permissions import BasePermission

class IsAuthor(BasePermission):
    """
    Allows access only to users with role = 'author'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', '') == 'author'