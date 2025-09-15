from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
import os
import json
from decimal import Decimal

class UserProfile(models.Model):
    """Extended user profile with card number information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    card_number = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\d{4}$', 'Card number must be exactly 4 digits')],
        help_text="Last 4 digits of the user's credit card"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.card_number or 'No card'}"
    
    @property
    def display_name(self):
        """Return user's full name or username"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def primary_role(self):
        """Return the user's primary role/group"""
        groups = self.user.groups.all()
        if groups.exists():
            return groups.first().name
        return 'No Role'
    
    @property
    def all_roles(self):
        """Return all user roles/groups"""
        return [group.name for group in self.user.groups.all()]

class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files/')
    file_type = models.CharField(max_length=50, blank=True)
    size = models.BigIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    # Metadata fields for file renaming
    project = models.CharField(max_length=255, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    date = models.CharField(max_length=20, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    total = models.CharField(max_length=20, blank=True, default='$0.00')
    
    # Payment tracking
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, blank=True)  # 'check' or 'credit_card'
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction attachment
    attached_transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='attached_files')
    
    # Approval workflow
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('on_hold', 'On Hold'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    approval_comment = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_files')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Class assignment for approval
    selected_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_files', help_text="Class selected during approval process")
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
            # Extract file extension for file_type
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lower() if ext else 'unknown'
        super().save(*args, **kwargs)
    
    @property
    def file_size_display(self):
        """Return human readable file size"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, blank=True)
    aliases = models.JSONField(default=list, blank=True)
    builders_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Superintendent assignment
    superintendents = models.ManyToManyField(User, blank=True, related_name='assigned_projects', limit_choices_to={'groups__name': 'Superintendent'})
    
    class Meta:
        ordering = ['-last_used', '-updated_at', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def assigned_superintendents(self):
        """Return list of assigned superintendents"""
        return self.superintendents.all()
    
    @classmethod
    def import_from_json(cls, json_file_path):
        """Import projects from JSON file"""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        imported_count = 0
        for project_data in data.get('projects', []):
            # Skip projects without names
            if not project_data.get('name'):
                continue
                
            # Create or update project
            project, created = cls.objects.get_or_create(
                name=project_data['name'],
                defaults={
                    'address': project_data.get('address', ''),
                    'aliases': project_data.get('aliases', []),
                    'builders_fee': project_data.get('builders_fee'),
                    'usage_count': project_data.get('usage_count', 0),
                }
            )
            
            if created:
                imported_count += 1
            else:
                # Update existing project
                project.address = project_data.get('address', project.address)
                project.aliases = project_data.get('aliases', project.aliases)
                project.builders_fee = project_data.get('builders_fee', project.builders_fee)
                project.usage_count = project_data.get('usage_count', project.usage_count)
                project.save()
        
        return imported_count

class Vendor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=100, default='Other')
    aliases = models.JSONField(default=list, blank=True)
    classes = models.ManyToManyField('Class', blank=True, related_name='vendors', help_text="Classes this vendor belongs to")
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, default='manual')
    
    class Meta:
        ordering = ['-last_used', '-updated_at', 'name']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def import_from_json(cls, json_file_path):
        """Import vendors from JSON file"""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        imported_count = 0
        for vendor_data in data.get('vendors', []):
            # Skip vendors without names
            if not vendor_data.get('name'):
                continue
                
            # Create or update vendor
            vendor, created = cls.objects.get_or_create(
                name=vendor_data['name'],
                defaults={
                    'category': vendor_data.get('category', 'Other'),
                    'aliases': vendor_data.get('aliases', []),
                    'usage_count': vendor_data.get('usage_count', 0),
                    'source': vendor_data.get('source', 'manual'),
                }
            )
            
            if created:
                imported_count += 1
            else:
                # Update existing vendor
                vendor.category = vendor_data.get('category', vendor.category)
                vendor.aliases = vendor_data.get('aliases', vendor.aliases)
                vendor.usage_count = vendor_data.get('usage_count', vendor.usage_count)
                vendor.source = vendor_data.get('source', vendor.source)
                vendor.save()
        
        return imported_count

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('CHARGE', 'Charge'),
        ('CREDIT', 'Credit'),
        ('PAYMENT', 'Payment'),
        ('REFUND', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('MATCHED', 'Matched'),
        ('UNMATCHED', 'Unmatched'),
        ('PENDING', 'Pending'),
    ]
    
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='CHARGE')
    card_holder = models.CharField(max_length=100)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNMATCHED')
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.date} - {self.description} - ${self.amount}"
    
    @property
    def amount_display(self):
        """Return formatted amount with + or - prefix"""
        if self.amount >= 0:
            return f"+${self.amount:,.2f}"
        else:
            return f"-${abs(self.amount):,.2f}"
    
    @property
    def is_positive(self):
        """Check if amount is positive"""
        return self.amount >= 0

class Class(models.Model):
    """Class model for categorizing vendors and invoices with hierarchical structure"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Optional description of this class")
    color = models.CharField(
        max_length=7, 
        default='#3B82F6', 
        help_text="Hex color code for UI display (e.g., #3B82F6)"
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        help_text="Parent class for hierarchical organization"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['parent__name', 'name']
        verbose_name_plural = 'Classes'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name
    
    @property
    def vendor_count(self):
        """Return the number of vendors assigned to this class"""
        return self.vendors.count()
    
    @property
    def is_parent(self):
        """Check if this class has children"""
        return self.children.exists()
    
    @property
    def is_child(self):
        """Check if this class has a parent"""
        return self.parent is not None
    
    @property
    def full_name(self):
        """Return the full hierarchical name"""
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name
    
    @property
    def display_name(self):
        """Return display name with proper indentation for children"""
        if self.parent:
            return f"  └─ {self.name}"
        return self.name
