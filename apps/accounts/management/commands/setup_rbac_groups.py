"""
Management command to set up RBAC groups and permissions.

Run this command after migrations to initialize the permission system:
    python manage.py setup_rbac_groups
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Initialize RBAC groups with appropriate permissions for HMS'

    # Define groups and their permissions
    # Format: group_name: [list of permission codenames]
    # Use '*' for all permissions on a model
    GROUP_PERMISSIONS = {
        'Super Admin': ['*'],  # All permissions
        
        'Hospital Administrator': [
            # View all
            'view_customuser', 'view_profile', 'view_department',
            'view_patient', 'view_appointment', 'view_medicalrecord',
            'view_prescription', 'view_labtest', 'view_labresult',
            'view_medicine', 'view_invoice', 'view_payment',
            'view_bed', 'view_ward', 'view_auditlog',
            # Change non-clinical
            'change_customuser', 'change_profile', 'change_department',
            'change_patient', 'change_appointment',
            'change_medicine', 'change_invoice', 'change_payment',
            'change_bed', 'change_ward',
            # Add non-clinical
            'add_customuser', 'add_profile', 'add_department',
            'add_patient', 'add_appointment',
            'add_medicine', 'add_invoice', 'add_payment',
            'add_bed', 'add_ward',
        ],
        
        'Receptionist': [
            # Patient management
            'add_patient', 'change_patient', 'view_patient',
            # Appointments
            'add_appointment', 'change_appointment', 'view_appointment',
            # View only for others
            'view_department', 'view_customuser', 'view_profile',
        ],
        
        'Doctor': [
            # Medical records
            'add_medicalrecord', 'change_medicalrecord', 'view_medicalrecord',
            # Prescriptions
            'add_prescription', 'change_prescription', 'view_prescription',
            # Appointments
            'view_appointment', 'change_appointment',
            # Patients
            'view_patient', 'change_patient',
            # Lab
            'add_labtest', 'view_labtest', 'view_labresult', 'change_labresult',
            # View staff
            'view_customuser', 'view_profile', 'view_department',
        ],
        
        'Nurse': [
            # Vitals and basic patient care
            'view_patient', 'change_patient',
            # Appointments
            'view_appointment',
            # Admissions
            'change_bed', 'view_bed', 'view_ward', 'change_ward',
            # View medical records
            'view_medicalrecord', 'view_prescription',
            # View staff
            'view_customuser', 'view_profile', 'view_department',
        ],
        
        'Pharmacist': [
            # Medicine inventory
            'add_medicine', 'change_medicine', 'view_medicine',
            # View prescriptions
            'view_prescription', 'change_prescription',
            # View patients
            'view_patient',
            # Inventory
            'add_inventory', 'change_inventory', 'view_inventory',
        ],
        
        'Laboratory Technician': [
            # Lab tests
            'add_labtest', 'change_labtest', 'view_labtest',
            'add_labresult', 'change_labresult', 'view_labresult',
            # View requests
            'view_patient', 'view_medicalrecord',
        ],
        
        'Accountant': [
            # Billing
            'add_invoice', 'change_invoice', 'view_invoice',
            'add_payment', 'change_payment', 'view_payment',
            # View patients
            'view_patient', 'view_appointment',
            # Reports
            'view_report',
        ],
        
        'Inventory Manager': [
            # Full inventory control
            'add_medicine', 'change_medicine', 'delete_medicine', 'view_medicine',
            'add_inventory', 'change_inventory', 'delete_inventory', 'view_inventory',
            # Suppliers (if exists)
            'add_supplier', 'change_supplier', 'delete_supplier', 'view_supplier',
            # View related
            'view_prescription', 'view_patient',
        ],
    }

    def handle(self, *args, **options):
        self.stdout.write('Setting up RBAC groups and permissions...')
        
        # Create or update groups
        for group_name, perm_codenames in self.GROUP_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(f'Created group: {group_name}')
            else:
                self.stdout.write(f'Updated group: {group_name}')
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Skip permission assignment for Super Admin (they get all via is_superuser)
            if group_name == 'Super Admin':
                continue
            
            # Assign permissions
            for codename in perm_codenames:
                try:
                    # Handle wildcard for specific models
                    if codename.endswith('*'):
                        model = codename.replace('*', '')
                        content_types = ContentType.objects.filter(model__startswith=model)
                        for ct in content_types:
                            perms = Permission.objects.filter(content_type=ct)
                            group.permissions.add(*perms)
                    else:
                        perm = Permission.objects.get(codename=codename)
                        group.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission not found: {codename}'),
                        ending=''
                    )
            
            group.save()
        
        self.stdout.write(self.style.SUCCESS('\nRBAC groups setup completed successfully!'))
        self.stdout.write(self.style.SUCCESS('\nGroups created:'))
        for group_name in self.GROUP_PERMISSIONS.keys():
            self.stdout.write(f'  - {group_name}')
        
        self.stdout.write(self.style.WARNING('\nNote: Remember to assign users to these groups.'))
