from django.contrib import admin
from .models import File, Project, Vendor, Transaction

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'file_size_display', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at', 'uploaded_by']
    search_fields = ['name', 'description']
    readonly_fields = ['size', 'file_type', 'uploaded_at']
    ordering = ['-uploaded_at']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'builders_fee', 'usage_count', 'last_used', 'updated_at']
    list_filter = ['builders_fee', 'last_used', 'updated_at']
    search_fields = ['name', 'address', 'aliases']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-last_used', '-updated_at', 'name']

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'usage_count', 'last_used', 'updated_at']
    list_filter = ['category', 'last_used', 'updated_at', 'source']
    search_fields = ['name', 'aliases']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-last_used', '-updated_at', 'name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount_display', 'description', 'transaction_type', 'card_holder', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'date', 'created_at']
    search_fields = ['description', 'card_holder', 'amount']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
