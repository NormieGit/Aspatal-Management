"""
Selectors for accounts app - reusable database queries.
"""
from typing import Optional, List
from django.db.models import Q
from .models import CustomUser, Profile, Department


class UserSelectors:
    """Database query selectors for User model."""

    @staticmethod
    def get_by_username_or_email(username_or_email: str) -> Optional[CustomUser]:
        """Get user by username or email address."""
        try:
            return CustomUser.objects.get(
                Q(username=username_or_email) | 
                Q(email=username_or_email.lower())
            )
        except CustomUser.DoesNotExist:
            return None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[CustomUser]:
        """Get user by ID with profile prefetched."""
        try:
            return CustomUser.objects.select_related('profile').get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None

    @staticmethod
    def get_all_active() -> List[CustomUser]:
        """Get all active users with profiles."""
        return CustomUser.objects.filter(
            is_active=True
        ).select_related('profile').order_by('date_joined')

    @staticmethod
    def get_by_role(role: str) -> List[CustomUser]:
        """Get all users with a specific role."""
        return CustomUser.objects.filter(
            is_active=True,
            profile__role=role
        ).select_related('profile').order_by('date_joined')


class ProfileSelectors:
    """Database query selectors for Profile model."""

    @staticmethod
    def get_by_user(user: CustomUser) -> Optional[Profile]:
        """Get profile for a user."""
        try:
            return Profile.objects.select_related('department').get(user=user)
        except Profile.DoesNotExist:
            return None

    @staticmethod
    def get_by_department(department_id: int) -> List[Profile]:
        """Get all profiles in a department."""
        return Profile.objects.filter(
            department_id=department_id
        ).select_related('user', 'department').order_by('user__last_name')

    @staticmethod
    def get_by_role(role: str) -> List[Profile]:
        """Get all profiles with a specific role."""
        return Profile.objects.filter(
            role=role
        ).select_related('user', 'department').order_by('user__last_name')


class DepartmentSelectors:
    """Database query selectors for Department model."""

    @staticmethod
    def get_all_active() -> List[Department]:
        """Get all active departments."""
        return Department.objects.filter(
            is_active=True
        ).order_by('name')

    @staticmethod
    def get_by_id(department_id: int) -> Optional[Department]:
        """Get department by ID."""
        try:
            return Department.objects.get(pk=department_id)
        except Department.DoesNotExist:
            return None

    @staticmethod
    def get_by_code(code: str) -> Optional[Department]:
        """Get department by code."""
        try:
            return Department.objects.get(code=code)
        except Department.DoesNotExist:
            return None
