from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, DoctorProfile


class Appointment(models.Model):
    """Appointment model for patient-doctor scheduling."""
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        NO_SHOW = 'no_show', _('No Show')
    
    class PriorityChoices(models.TextChoices):
        ROUTINE = 'routine', _('Routine')
        URGENT = 'urgent', _('Urgent')
        EMERGENCY = 'emergency', _('Emergency')
    
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_appointments',
        limit_choices_to={'role': User.RoleChoices.PATIENT},
        db_index=True
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_appointments',
        limit_choices_to={'role': User.RoleChoices.DOCTOR},
        db_index=True
    )
    appointment_date = models.DateField(_('appointment date'), db_index=True)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True
    )
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.ROUTINE
    )
    appointment_type = models.CharField(_('appointment type'), max_length=100, default='General Consultation')
    reason_for_visit = models.TextField(_('reason for visit'), max_length=500)
    notes = models.TextField(_('notes'), blank=True)
    booked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='booked_appointments',
        null=True,
        editable=False
    )
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='cancelled_appointments',
        null=True,
        blank=True
    )
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)
    reminder_sent = models.BooleanField(_('reminder sent'), default=False)
    check_in_time = models.DateTimeField(_('check in time'), null=True, blank=True)
    check_out_time = models.DateTimeField(_('check out time'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('appointment')
        verbose_name_plural = _('appointments')
        ordering = ['-appointment_date', '-start_time']
        unique_together = ['doctor', 'appointment_date', 'start_time']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['appointment_date', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Appointment: {self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {self.appointment_date} at {self.start_time}"
    
    def clean(self):
        """Validate appointment data."""
        from django.core.exceptions import ValidationError
        
        if self.start_time >= self.end_time:
            raise ValidationError(_('End time must be after start time.'))
        
        # Check for overlapping appointments
        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            status__in=[self.StatusChoices.CONFIRMED, self.StatusChoices.PENDING, self.StatusChoices.IN_PROGRESS],
        ).exclude(pk=self.pk)
        
        for appointment in overlapping:
            if not (self.end_time <= appointment.start_time or self.start_time >= appointment.end_time):
                raise ValidationError(_('This time slot conflicts with an existing appointment.'))


class AppointmentSlot(models.Model):
    """Available time slots for doctors."""
    
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='available_slots',
        db_index=True
    )
    slot_date = models.DateField(_('slot date'), db_index=True)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    is_available = models.BooleanField(_('is available'), default=True)
    is_booked = models.BooleanField(_('is booked'), default=False)
    booked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='booked_slots',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('appointment slot')
        verbose_name_plural = _('appointment slots')
        ordering = ['slot_date', 'start_time']
        unique_together = ['doctor', 'slot_date', 'start_time']
        indexes = [
            models.Index(fields=['slot_date', 'is_available']),
            models.Index(fields=['doctor', 'is_available']),
        ]
    
    def __str__(self):
        return f"Slot: {self.doctor.user.get_full_name()} on {self.slot_date} at {self.start_time}"


class AppointmentHistory(models.Model):
    """Audit trail for appointment changes."""
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='history',
        db_index=True
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointment_history'
    )
    change_type = models.CharField(_('change type'), max_length=50)
    old_value = models.TextField(_('old value'), blank=True)
    new_value = models.TextField(_('new value'), blank=True)
    changed_at = models.DateTimeField(_('changed at'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('appointment history')
        verbose_name_plural = _('appointment histories')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['appointment', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.change_type} on {self.appointment} at {self.changed_at}"
