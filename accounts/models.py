from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with role-based access control."""
    
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        DOCTOR = 'doctor', _('Doctor')
        NURSE = 'nurse', _('Nurse')
        RECEPTIONIST = 'receptionist', _('Receptionist')
        PATIENT = 'patient', _('Patient')
    
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT,
        db_index=True
    )
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    zip_code = models.CharField(_('zip code'), max_length=10, blank=True)
    country = models.CharField(_('country'), max_length=100, default='USA')
    profile_picture = models.ImageField(_('profile picture'), upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_verified = models.BooleanField(_('is verified'), default=False)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.RoleChoices.ADMIN
    
    @property
    def is_doctor(self):
        return self.role == self.RoleChoices.DOCTOR
    
    @property
    def is_nurse(self):
        return self.role == self.RoleChoices.NURSE
    
    @property
    def is_receptionist(self):
        return self.role == self.RoleChoices.RECEPTIONIST
    
    @property
    def is_patient(self):
        return self.role == self.RoleChoices.PATIENT


class DoctorProfile(models.Model):
    """Extended profile information for doctors."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile', primary_key=True)
    specialization = models.CharField(_('specialization'), max_length=100, db_index=True)
    license_number = models.CharField(_('license number'), max_length=50, unique=True, db_index=True)
    years_of_experience = models.PositiveIntegerField(_('years of experience'), default=0)
    education = models.TextField(_('education'), blank=True)
    certifications = models.TextField(_('certifications'), blank=True)
    bio = models.TextField(_('bio'), blank=True, max_length=1000)
    consultation_fee = models.DecimalField(_('consultation fee'), max_digits=10, decimal_places=2, default=0.00)
    available_days = models.CharField(_('available days'), max_length=100, default='Monday-Friday')
    available_start_time = models.TimeField(_('available start time'), default='09:00:00')
    available_end_time = models.TimeField(_('available end time'), default='17:00:00')
    appointment_duration = models.PositiveIntegerField(_('appointment duration (minutes)'), default=30)
    is_available = models.BooleanField(_('is available'), default=True)
    rating = models.DecimalField(_('rating'), max_digits=3, decimal_places=2, default=0.00, blank=True)
    total_reviews = models.PositiveIntegerField(_('total reviews'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('doctor profile')
        verbose_name_plural = _('doctor profiles')
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['specialization']),
            models.Index(fields=['license_number']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"


class PatientProfile(models.Model):
    """Extended profile information for patients."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', primary_key=True)
    blood_group = models.CharField(_('blood group'), max_length=5, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ], blank=True)
    gender = models.CharField(_('gender'), max_length=10, choices=[
        ('male', 'Male'), ('female', 'Female'), ('other', 'Other'),
    ], blank=True)
    height = models.DecimalField(_('height (cm)'), max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(_('weight (kg)'), max_digits=5, decimal_places=2, null=True, blank=True)
    emergency_contact_name = models.CharField(_('emergency contact name'), max_length=100, blank=True)
    emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=15, blank=True)
    emergency_contact_relation = models.CharField(_('emergency contact relation'), max_length=50, blank=True)
    insurance_provider = models.CharField(_('insurance provider'), max_length=100, blank=True)
    insurance_policy_number = models.CharField(_('insurance policy number'), max_length=50, blank=True)
    medical_history_summary = models.TextField(_('medical history summary'), blank=True)
    allergies = models.TextField(_('allergies'), blank=True, help_text=_("Comma-separated list of allergies"))
    current_medications = models.TextField(_('current medications'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('patient profile')
        verbose_name_plural = _('patient profiles')
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['blood_group']),
            models.Index(fields=['insurance_policy_number']),
        ]
    
    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"


class NurseProfile(models.Model):
    """Extended profile information for nurses."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nurse_profile', primary_key=True)
    department = models.CharField(_('department'), max_length=100, db_index=True)
    license_number = models.CharField(_('license number'), max_length=50, unique=True, db_index=True)
    shift = models.CharField(_('shift'), max_length=20, choices=[
        ('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night'),
    ], default='morning')
    years_of_experience = models.PositiveIntegerField(_('years of experience'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('nurse profile')
        verbose_name_plural = _('nurse profiles')
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['license_number']),
        ]
    
    def __str__(self):
        return f"Nurse: {self.user.get_full_name()} - {self.department}"


class ReceptionistProfile(models.Model):
    """Extended profile information for receptionists."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionist_profile', primary_key=True)
    employee_id = models.CharField(_('employee ID'), max_length=20, unique=True, db_index=True)
    department = models.CharField(_('department'), max_length=100, default='Front Desk')
    shift = models.CharField(_('shift'), max_length=20, choices=[
        ('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night'),
    ], default='morning')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('receptionist profile')
        verbose_name_plural = _('receptionist profiles')
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return f"Receptionist: {self.user.get_full_name()} - {self.employee_id}"
