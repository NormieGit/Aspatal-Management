from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class MedicalRecord(models.Model):
    """Medical record model for patient health information."""
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medical_records',
        limit_choices_to={'role': User.RoleChoices.PATIENT},
        db_index=True
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_medical_records',
        limit_choices_to={'role': User.RoleChoices.DOCTOR},
        db_index=True
    )
    record_type = models.CharField(_('record type'), max_length=50, choices=[
        ('consultation', 'Consultation'),
        ('diagnosis', 'Diagnosis'),
        ('treatment', 'Treatment'),
        ('surgery', 'Surgery'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging'),
        ('vaccination', 'Vaccination'),
        ('other', 'Other'),
    ], db_index=True)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    diagnosis = models.TextField(_('diagnosis'), blank=True)
    treatment_plan = models.TextField(_('treatment plan'), blank=True)
    prescriptions = models.TextField(_('prescriptions'), blank=True, help_text=_("JSON or structured text of prescribed medications"))
    lab_orders = models.TextField(_('lab orders'), blank=True)
    lab_results = models.TextField(_('lab results'), blank=True)
    imaging_results = models.TextField(_('imaging results'), blank=True)
    vital_signs = models.TextField(_('vital signs'), blank=True, help_text=_("BP, Temperature, Pulse, etc."))
    allergies_noted = models.TextField(_('allergies noted'), blank=True)
    follow_up_required = models.BooleanField(_('follow-up required'), default=False)
    follow_up_date = models.DateField(_('follow-up date'), null=True, blank=True)
    is_confidential = models.BooleanField(_('is confidential'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('medical record')
        verbose_name_plural = _('medical records')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['doctor', '-created_at']),
            models.Index(fields=['record_type']),
            models.Index(fields=['is_confidential']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.patient.get_full_name()} ({self.created_at.strftime('%Y-%m-%d')})"


class Prescription(models.Model):
    """Prescription model for medication tracking."""
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        db_index=True
    )
    medication_name = models.CharField(_('medication name'), max_length=200, db_index=True)
    dosage = models.CharField(_('dosage'), max_length=100)
    frequency = models.CharField(_('frequency'), max_length=100, help_text=_("e.g., Twice daily, Every 8 hours"))
    duration = models.CharField(_('duration'), max_length=100, help_text=_("e.g., 7 days, 2 weeks"))
    instructions = models.TextField(_('instructions'), blank=True, help_text=_("Take with food, Avoid alcohol, etc."))
    quantity = models.PositiveIntegerField(_('quantity'), default=0)
    refills_allowed = models.PositiveIntegerField(_('refills allowed'), default=0)
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescribed_medications',
        limit_choices_to={'role': User.RoleChoices.DOCTOR}
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('prescription')
        verbose_name_plural = _('prescriptions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medical_record']),
            models.Index(fields=['medication_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} - {self.medical_record.patient.get_full_name()}"


class LabTest(models.Model):
    """Lab test model for diagnostic tests."""
    
    class StatusChoices(models.TextChoices):
        ORDERED = 'ordered', _('Ordered')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='lab_tests',
        db_index=True
    )
    test_name = models.CharField(_('test name'), max_length=200, db_index=True)
    test_code = models.CharField(_('test code'), max_length=50, blank=True)
    description = models.TextField(_('description'), blank=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ORDERED,
        db_index=True
    )
    ordered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ordered_lab_tests',
        limit_choices_to={'role': User.RoleChoices.DOCTOR}
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='performed_lab_tests',
        null=True,
        blank=True,
        limit_choices_to={'role__in': [User.RoleChoices.DOCTOR, User.RoleChoices.NURSE]}
    )
    sample_collection_date = models.DateTimeField(_('sample collection date'), null=True, blank=True)
    result_date = models.DateTimeField(_('result date'), null=True, blank=True)
    results = models.TextField(_('results'), blank=True)
    reference_range = models.TextField(_('reference range'), blank=True)
    units = models.CharField(_('units'), max_length=50, blank=True)
    is_abnormal = models.BooleanField(_('is abnormal'), default=False)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('lab test')
        verbose_name_plural = _('lab tests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medical_record']),
            models.Index(fields=['test_name']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.test_name} - {self.medical_record.patient.get_full_name()}"


class MedicalAttachment(models.Model):
    """File attachments for medical records."""
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='attachments',
        db_index=True
    )
    file = models.FileField(_('file'), upload_to='medical_attachments/%Y/%m/%d/')
    file_type = models.CharField(_('file type'), max_length=50, choices=[
        ('document', 'Document'),
        ('image', 'Image'),
        ('lab_report', 'Lab Report'),
        ('imaging', 'Imaging'),
        ('other', 'Other'),
    ])
    description = models.TextField(_('description'), blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    is_confidential = models.BooleanField(_('is confidential'), default=False)
    
    class Meta:
        verbose_name = _('medical attachment')
        verbose_name_plural = _('medical attachments')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['medical_record']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        return f"{self.file.name} - {self.medical_record.title}"


class AuditLog(models.Model):
    """Audit trail for medical record access and modifications (HIPAA compliance)."""
    
    class ActionChoices(models.TextChoices):
        VIEW = 'view', _('View')
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        EXPORT = 'export', _('Export')
        PRINT = 'print', _('Print')
    
    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True
    )
    action = models.CharField(
        _('action'),
        max_length=20,
        choices=ActionChoices.choices,
        db_index=True
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medical_audit_logs'
    )
    performed_at = models.DateTimeField(_('performed at'), auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    details = models.TextField(_('details'), blank=True)
    
    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['record', '-performed_at']),
            models.Index(fields=['performed_by', '-performed_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.record} by {self.performed_by} at {self.performed_at}"
