"""
Authentication and user management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, FormView, View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    ProfileUpdateForm, 
    UserUpdateForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)
from .models import Profile
from .services import AuthenticationService
from .selectors import UserSelectors

CustomUser = get_user_model()


@method_decorator(sensitive_post_parameters(), name='dispatch')
class LoginView(DjangoLoginView):
    """
    Custom login view with account lockout protection.
    """
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Log in the user and record successful login."""
        user = form.get_user()
        AuthenticationService.login_user(self.request, user)
        
        # Record successful login for audit
        user.record_successful_login()
        
        messages.success(
            self.request,
            f'Welcome back, {user.first_name or user.username}!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Record failed login attempt."""
        username = form.cleaned_data.get('username')
        if username:
            user = UserSelectors.get_by_username_or_email(username)
            if user:
                user.record_failed_login()
        return super().form_invalid(form)


class LogoutView(LoginRequiredMixin, DjangoLogoutView):
    """
    Custom logout view with success message.
    """
    next_page = 'accounts:login'
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.info(request, 'You have been logged out successfully.')
        return response


class RegisterView(CreateView):
    """
    User registration view.
    """
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """Create user and send verification email."""
        user = form.save(commit=False)
        user.is_active = False  # Require email verification
        user.save()
        
        # Create profile
        role = form.cleaned_data.get('role')
        department = form.cleaned_data.get('department')
        
        Profile.objects.create(
            user=user,
            role=role,
            department=department
        )
        
        # Send verification email
        AuthenticationService.send_verification_email(user)
        
        messages.success(
            self.request,
            'Registration successful! Please check your email to verify your account.'
        )
        return redirect('accounts:login')


class PasswordResetRequestView(FormView):
    """
    Password reset request view.
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset_request.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """Send password reset email."""
        email = form.cleaned_data.get('email')
        AuthenticationService.reset_password_request(email)
        
        messages.success(
            self.request,
            'If an account exists with that email, a password reset link has been sent.'
        )
        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    """
    Password reset confirmation view.
    """
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        uidb64 = self.kwargs.get('uidb64')
        token = self.kwargs.get('token')
        
        # Get user from uidb64
        try:
            from django.utils.http import urlsafe_base64_decode
            from django.utils.encoding import force_str
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=user_id)
            kwargs['user'] = user
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None
        
        kwargs['user'] = user
        return kwargs

    def form_valid(self, form):
        """Reset password."""
        uidb64 = self.kwargs.get('uidb64')
        token = self.kwargs.get('token')
        new_password = form.cleaned_data.get('new_password1')
        
        success, error = AuthenticationService.confirm_password_reset(
            uidb64, token, new_password
        )
        
        if success:
            messages.success(
                self.request,
                'Password reset successful! You can now log in with your new password.'
            )
            return super().form_valid(form)
        else:
            messages.error(self.request, error)
            return self.form_invalid(form)


class VerifyEmailView(View):
    """
    Email verification view.
    """
    def get(self, request, uidb64, token):
        """Verify email and redirect to login."""
        success, error = AuthenticationService.verify_email(uidb64, token)
        
        if success:
            messages.success(
                request,
                'Email verified successfully! You can now log in.'
            )
        else:
            messages.error(request, error)
        
        return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, View):
    """
    User profile view.
    """
    def get(self, request):
        """Display user profile."""
        profile = request.user.profile
        return render(request, 'accounts/profile.html', {'profile': profile})


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Profile update view.
    """
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        """Get current user's profile."""
        return self.request.user.profile


class ChangePasswordView(LoginRequiredMixin, FormView):
    """
    Change password view for logged-in users.
    """
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')

    def get_form_class(self):
        from django.contrib.auth.forms import PasswordChangeForm
        return PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Change password."""
        form.save()
        messages.success(
            self.request,
            'Password changed successfully!'
        )
        return super().form_valid(form)
