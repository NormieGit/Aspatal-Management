"""
Authentication services - Business logic for user management.
"""
from typing import Optional, Tuple
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.db import transaction
from .models import Profile, Department

CustomUser = get_user_model()


class AuthenticationService:
    """
    Service class for authentication-related business logic.
    
    All authentication operations should go through this service
    to ensure consistent security and logging.
    """

    @staticmethod
    @transaction.atomic
    def create_user(
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str,
        department_id: Optional[int] = None,
        phone: Optional[str] = None,
        is_staff: bool = False,
        is_verified: bool = False
    ) -> CustomUser:
        """
        Create a new user with profile.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Raw password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            role: Role from Profile.ROLE_CHOICES
            department_id: Optional department ID
            phone: Optional phone number
            is_staff: Whether user has staff privileges
            is_verified: Whether email is pre-verified
            
        Returns:
            Created CustomUser instance
            
        Raises:
            IntegrityError: If username or email already exists
        """
        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_staff=is_staff,
            is_verified=is_verified
        )
        
        # Create profile
        department = None
        if department_id:
            department = Department.objects.get(id=department_id)
        
        Profile.objects.create(
            user=user,
            role=role,
            department=department
        )
        
        return user

    @staticmethod
    def authenticate_user(username_or_email: str, password: str) -> Tuple[Optional[CustomUser], str]:
        """
        Authenticate a user and return user object or error message.
        
        Args:
            username_or_email: Username or email address
            password: Raw password
            
        Returns:
            Tuple of (User object or None, error message or empty string)
        """
        # Try to find user by username or email
        try:
            user = CustomUser.objects.get(
                models.Q(username=username_or_email) | 
                models.Q(email=username_or_email.lower())
            )
        except CustomUser.DoesNotExist:
            return None, "Invalid credentials."
        
        # Check if account is locked
        if user.is_locked_out():
            return None, "Account is temporarily locked due to multiple failed attempts."
        
        # Verify password
        if not user.check_password(password):
            user.record_failed_login()
            return None, "Invalid credentials."
        
        # Check if user is active
        if not user.is_active:
            return None, "Account is deactivated. Contact administrator."
        
        # Check if email is verified
        if not user.is_verified:
            return None, "Please verify your email address before logging in."
        
        # Success - record successful login
        user.record_successful_login()
        return user, ""

    @staticmethod
    def login_user(request, user: CustomUser) -> None:
        """
        Perform Django login with session creation.
        """
        auth_login(request, user)

    @staticmethod
    def logout_user(request) -> None:
        """
        Perform Django logout with session cleanup.
        """
        auth_logout(request)

    @staticmethod
    @transaction.atomic
    def reset_password_request(email: str) -> bool:
        """
        Initiate password reset process.
        
        Args:
            email: User's email address
            
        Returns:
            True if email was sent (even if user doesn't exist, for security)
        """
        try:
            user = CustomUser.objects.get(email=email.lower(), is_active=True)
        except CustomUser.DoesNotExist:
            # Return True anyway to prevent user enumeration
            return True
        
        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build reset URL
        reset_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:8000'}/accounts/reset-password/{uid}/{token}/"
        
        # Send email
        subject = "Password Reset Request - HMS"
        message = f"""
Hello {user.first_name or user.username},

You requested a password reset for your Hospital Management System account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
HMS Team
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@hms.com',
                [user.email],
                fail_silently=False
            )
            return True
        except Exception:
            # Log error in production
            return False

    @staticmethod
    @transaction.atomic
    def confirm_password_reset(uid: str, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Confirm and execute password reset.
        
        Args:
            uid: Base64 encoded user ID
            token: Password reset token
            new_password: New raw password
            
        Returns:
            Tuple of (success boolean, error message)
        """
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return False, "Invalid reset link."
        
        # Validate token
        if not default_token_generator.check_token(user, token):
            return False, "Invalid or expired reset link."
        
        # Set new password
        user.change_password(new_password)
        return True, ""

    @staticmethod
    def verify_email(uid: str, token: str) -> Tuple[bool, str]:
        """
        Verify user email address.
        
        Args:
            uid: Base64 encoded user ID
            token: Verification token
            
        Returns:
            Tuple of (success boolean, error message)
        """
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return False, "Invalid verification link."
        
        # Validate token
        if not default_token_generator.check_token(user, token):
            return False, "Invalid or expired verification link."
        
        # Mark as verified
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return True, ""

    @staticmethod
    def send_verification_email(user: CustomUser) -> bool:
        """
        Send email verification email.
        
        Args:
            user: User instance
            
        Returns:
            True if email was sent successfully
        """
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verify_url = f"/accounts/verify-email/{uid}/{token}/"
        
        subject = "Verify Your Email - HMS"
        message = f"""
Hello {user.first_name or user.username},

Welcome to the Hospital Management System!

Please click the link below to verify your email address:
{verify_url}

Best regards,
HMS Team
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@hms.com',
                [user.email],
                fail_silently=False
            )
            return True
        except Exception:
            return False
