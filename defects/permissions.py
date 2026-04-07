from rest_framework import permissions

class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Product Owner').exists()

class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Developer').exists()

class IsTester(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Tester').exists()