from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Invoice(models.Model):
    """Invoice model for billing patients."""
    
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending')
        PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
        PAID = 'paid', _('Paid')
        OVERDUE = 'overdue', _('Overdue')
        CANCELLED = 'cancelled', _('Cancelled')
    
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True, db_index=True)
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        limit_choices_to={'role': User.RoleChoices.PATIENT},
        db_index=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_invoices',
        null=True,
        limit_choices_to={'role__in': [User.RoleChoices.ADMIN, User.RoleChoices.RECEPTIONIST]}
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        related_name='invoices',
        null=True,
        blank=True
    )
    issue_date = models.DateField(_('issue date'), auto_now_add=True, db_index=True)
    due_date = models.DateField(_('due date'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True
    )
    subtotal = models.DecimalField(_('subtotal'), max_digits=10, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(_('tax rate (%)'), max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(_('tax amount'), max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(_('discount'), max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(_('amount paid'), max_digits=10, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(_('balance due'), max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(_('notes'), blank=True)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient.get_full_name()}"
    
    def calculate_totals(self):
        """Calculate invoice totals."""
        self.subtotal = sum(item.total for item self.items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount - self.discount
        self.balance_due = self.total_amount - self.amount_paid


class InvoiceItem(models.Model):
    """Line items for invoices."""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True
    )
    description = models.CharField(_('description'), max_length=300)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2)
    total = models.DecimalField(_('total'), max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('invoice item')
        verbose_name_plural = _('invoice items')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['invoice']),
        ]
    
    def __str__(self):
        return f"{self.description} - ${self.total}"
    
    def save(self, *args, **kwargs):
        """Calculate total before saving."""
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment model for tracking payments."""
    
    class PaymentMethodChoices(models.TextChoices):
        CASH = 'cash', _('Cash')
        CREDIT_CARD = 'credit_card', _('Credit Card')
        DEBIT_CARD = 'debit_card', _('Debit Card')
        CHECK = 'check', _('Check')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        INSURANCE = 'insurance', _('Insurance')
        ONLINE = 'online', _('Online')
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True
    )
    payment_number = models.CharField(_('payment number'), max_length=50, unique=True, db_index=True)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PaymentMethodChoices.choices,
        db_index=True
    )
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True)
    payment_date = models.DateTimeField(_('payment date'), auto_now_add=True, db_index=True)
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='received_payments',
        null=True
    )
    notes = models.TextField(_('notes'), blank=True)
    is_refunded = models.BooleanField(_('is refunded'), default=False)
    refund_date = models.DateTimeField(_('refund date'), null=True, blank=True)
    refund_reason = models.TextField(_('refund reason'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_date']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_number} - ${self.amount} for {self.invoice.invoice_number}"


class InsuranceClaim(models.Model):
    """Insurance claim model."""
    
    class StatusChoices(models.TextChoices):
        SUBMITTED = 'submitted', _('Submitted')
        UNDER_REVIEW = 'under_review', _('Under Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        PAID = 'paid', _('Paid')
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='insurance_claims',
        limit_choices_to={'role': User.RoleChoices.PATIENT}
    )
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name='insurance_claim'
    )
    insurance_provider = models.CharField(_('insurance provider'), max_length=100)
    policy_number = models.CharField(_('policy number'), max_length=50)
    claim_number = models.CharField(_('claim number'), max_length=50, unique=True, db_index=True)
    diagnosis_code = models.CharField(_('diagnosis code (ICD-10)'), max_length=20, blank=True)
    procedure_code = models.CharField(_('procedure code (CPT)'), max_length=20, blank=True)
    claim_amount = models.DecimalField(_('claim amount'), max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(_('approved amount'), max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.SUBMITTED,
        db_index=True
    )
    submitted_date = models.DateField(_('submitted date'), auto_now_add=True)
    processed_date = models.DateField(_('processed date'), null=True, blank=True)
    denial_reason = models.TextField(_('denial reason'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('insurance claim')
        verbose_name_plural = _('insurance claims')
        ordering = ['-submitted_date']
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['claim_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Claim {self.claim_number} - {self.patient.get_full_name()}"


class BillingAuditLog(models.Model):
    """Audit trail for billing operations."""
    
    class ActionChoices(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        PAYMENT_RECEIVED = 'payment_received', _('Payment Received')
        REFUND = 'refund', _('Refund')
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True
    )
    action = models.CharField(
        _('action'),
        max_length=30,
        choices=ActionChoices.choices,
        db_index=True
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='billing_audit_logs'
    )
    performed_at = models.DateTimeField(_('performed at'), auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    details = models.TextField(_('details'), blank=True)
    
    class Meta:
        verbose_name = _('billing audit log')
        verbose_name_plural = _('billing audit logs')
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['invoice', '-performed_at']),
            models.Index(fields=['performed_by', '-performed_at']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.invoice} by {self.performed_by} at {self.performed_at}"
