"""
Custom User Model for HMS.

Implements a secure, extensible user model with account lockout protection.
Uses Django's AbstractUser as base for full authentication compatibility.
"""
import bcrypt
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    """
    Custom User model extending AbstractUser.
    
    Features:
    - Email-based authentication (email is unique)
    - Phone number field
    - Account lockout after failed login attempts
    - Email verification tracking
    - Last login tracking
    
    Security:
    - Password hashing via Django's built-in system
    - Account lockout to prevent brute force attacks
    """
    email = models.EmailField(
        'Email Address',
        unique=True,
        db_index=True,
        help_text='Required. Enter a valid email address.'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='Optional phone number for contact.'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Indicates if the user email has been verified.'
    )
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text='Number of consecutive failed login attempts.'
    )
    locked_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Account lockout expiration time.'
    )
    last_password_change = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp of last password change.'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_full_name() or 'No Name'})"

    def save(self, *args, **kwargs):
        """
        Override save to normalize email and handle account lockout reset.
        """
        if self.email:
            self.email = self.email.lower().strip()
        
        # Reset lockout if manually unlocked by admin
        if not self.locked_until and self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            
        super().save(*args, **kwargs)

    def record_failed_login(self):
        """
        Record a failed login attempt and lock account if threshold exceeded.
        Threshold: 5 failed attempts results in 30-minute lockout.
        """
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def record_successful_login(self):
        """
        Reset failed login counter and clear lockout on successful login.
        """
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'locked_until', 'last_login'])

    def is_locked_out(self) -> bool:
        """
        Check if the account is currently locked out.
        Automatically unlocks if lockout period has expired.
        """
        if not self.locked_until:
            return False
        
        if timezone.now() >= self.locked_until:
            # Lockout period expired, reset
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_attempts', 'locked_until'])
            return False
        
        return True

    def change_password(self, raw_password):
        """
        Change password with proper hashing and timestamp update.
        """
        self.set_password(raw_password)
        self.last_password_change = timezone.now()
        self.save(update_fields=['password', 'last_password_change'])


class Profile(AbstractBaseModel):
    """
    Base profile model for all users.
    
    Contains common fields shared across all roles.
    Role-specific fields should be in separate models (DoctorProfile, NurseProfile, etc.).
    
    Relationships:
    - OneToOne with CustomUser (each user has exactly one profile)
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Hospital Administrator'),
        ('RECEPTIONIST', 'Receptionist'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('PHARMACIST', 'Pharmacist'),
        ('LAB_TECH', 'Laboratory Technician'),
        ('ACCOUNTANT', 'Accountant'),
        ('INVENTORY_MANAGER', 'Inventory Manager'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Associated user account.'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text='Primary role of the user.'
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        help_text='Department the user belongs to.'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Profile picture.'
    )
    bio = models.TextField(
        blank=True,
        max_length=500,
        help_text='Short biography or description.'
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text='Professional license number (for medical staff).'
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text='Date of birth.'
    )
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True,
        null=True,
        help_text='Gender.'
    )
    address = models.TextField(
        blank=True,
        max_length=500,
        help_text='Physical address.'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text='City.'
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text='State/Province.'
    )
    zip_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='ZIP/Postal code.'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='USA',
        help_text='Country.'
    )

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['user__email']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
        ]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.email} - {self.get_role_display()}"


class Department(AbstractBaseModel):
    """
    Department model for organizing hospital departments.
    
    Used to categorize staff, patients (for admissions), and services.
    
    Relationships:
    - Head of Department links to CustomUser (OneToOne, nullable)
    - Staff members link via Profile.department (ForeignKey)
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Department name.'
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text='Short code for the department (e.g., CARD, NEUR, PEDS).'
    )
    description = models.TextField(
        blank=True,
        max_length=500,
        help_text='Department description.'
    )
    head_of_department = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments_led',
        help_text='Head of this department.'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Indicates if the department is currently active.'
    )

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def get_staff_count(self) -> int:
        """Return the number of staff members in this department."""
        return self.staff_members.count()

    def clean(self):
        """
        Validate that head_of_department has appropriate permissions.
        This is called during form validation and admin save.
        """
        if self.head_of_department and not self.head_of_department.is_staff:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'Head of Department must be a staff member with admin access.'
            )
