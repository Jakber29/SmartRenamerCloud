from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator
from django.db import models
from functools import wraps
import json
import os
import csv
from decimal import Decimal
from datetime import datetime
from .models import File, Project, Vendor, Transaction, UserProfile, Class

def admin_or_staff_required(view_func):
    """Decorator to restrict access to admin/staff users only. Redirects superintendents to approvals page."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            # Check if user is a superintendent
            if request.user.groups.filter(name='Superintendent').exists():
                messages.info(request, 'You only have access to the Approvals page.')
                return redirect('approvals_list')
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('approvals_list')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def dashboard(request):
    # Redirect superintendents to approvals page
    if not request.user.is_staff and request.user.groups.filter(name='Superintendent').exists():
        return redirect('approvals_list')
    return render(request, "dashboard.html")

@login_required
@admin_or_staff_required
def file_manager(request):
    all_files = File.objects.all()
    
    # Separate files into processed and unprocessed
    unprocessed_files = []
    processed_files = []
    
    for file in all_files:
        # A file is considered "processed" if it has at least project, vendor, or date filled
        is_processed = bool(file.project or file.vendor or file.date)
        
        file_data = {
            'id': file.id,
            'name': file.name,
            'file_type': file.file_type,
            'file_size_display': file.file_size_display,
            'uploaded_at': file.uploaded_at.strftime('%b %d, %Y'),
            'description': file.description or '',
            'file': file.file.name if file.file else '',
            'project': file.project or '',
            'vendor': file.vendor or '',
            'date': file.date or '',
            'invoice_number': file.invoice_number or '',
            'total': file.total or '$0.00',
            'is_processed': is_processed
        }
        
        if is_processed:
            processed_files.append(file_data)
        else:
            unprocessed_files.append(file_data)
    
    # Convert to JSON for JavaScript
    files_json = unprocessed_files + processed_files
    
    return render(request, "file_manager.html", {
        "unprocessed_files": unprocessed_files,
        "processed_files": processed_files,
        "files_json": json.dumps(files_json)
    })

@login_required
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Create File object
            file_obj = File(
                name=uploaded_file.name,
                file=uploaded_file,
                uploaded_by=request.user,
                description=request.POST.get('description', '')
            )
            file_obj.save()
            messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
        else:
            messages.error(request, 'No file selected.')
        return redirect('file_manager')
    return redirect('file_manager')

@login_required
@xframe_options_exempt
def preview_file(request, file_id):
    """Serve file for iframe preview with X-Frame-Options exempt"""
    try:
        file_obj = File.objects.get(id=file_id)
        
        # Determine content type based on file extension
        if file_obj.file_type == '.pdf':
            content_type = 'application/pdf'
        elif file_obj.file_type in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_obj.file_type == '.png':
            content_type = 'image/png'
        elif file_obj.file_type == '.gif':
            content_type = 'image/gif'
        elif file_obj.file_type == '.webp':
            content_type = 'image/webp'
        else:
            raise Http404("File type not supported for preview")
        
        response = FileResponse(file_obj.file.open(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{file_obj.name}"'
        return response
    except File.DoesNotExist:
        raise Http404("File not found")

@login_required
def download_file(request, file_id):
    try:
        file_obj = File.objects.get(id=file_id)
        response = HttpResponse(file_obj.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
        return response
    except File.DoesNotExist:
        raise Http404("File not found")

@login_required
def delete_file(request, file_id):
    try:
        file_obj = File.objects.get(id=file_id)
        file_name = file_obj.name
        # Delete the actual file from storage
        if file_obj.file:
            file_obj.file.delete()
        # Delete the database record
        file_obj.delete()
        messages.success(request, f'File "{file_name}" deleted successfully!')
    except File.DoesNotExist:
        messages.error(request, 'File not found.')
    return redirect('file_manager')

@login_required
@require_http_methods(["POST"])
def rename_file(request):
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        project = data.get('project', '').strip()
        vendor = data.get('vendor', '').strip()
        date = data.get('date', '').strip()
        invoice_number = data.get('invoice_number', '').strip()
        total = data.get('total', '$0.00').strip()
        
        if not file_id:
            return JsonResponse({
                'success': False,
                'message': 'No file selected'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        
        # Generate new filename based on the pattern
        new_name_parts = []
        
        # Add project if provided
        if project:
            new_name_parts.append(project)
        
        # Add vendor if provided
        if vendor:
            new_name_parts.append(vendor)
        
        # Add date if provided
        if date:
            new_name_parts.append(date)
        
        # Add invoice number if provided
        if invoice_number:
            new_name_parts.append(invoice_number)
        
        # Add total if provided and not default
        if total and total != '$0.00':
            new_name_parts.append(total)
        
        if new_name_parts:
            # Get file extension
            _, ext = os.path.splitext(file_obj.name)
            new_name = ' - '.join(new_name_parts) + ext
            
            # Update the file name and save metadata
            file_obj.name = new_name
            file_obj.project = project
            file_obj.vendor = vendor
            file_obj.date = date
            file_obj.invoice_number = invoice_number
            file_obj.total = total
            file_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'File renamed to "{new_name}"',
                'new_name': new_name
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in at least one field to rename the file'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error renaming file: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def save_notes(request):
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        notes = data.get('notes', '')
        
        file_obj = get_object_or_404(File, id=file_id)
        file_obj.description = notes
        file_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notes saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving notes: {str(e)}'
        })

@login_required
@admin_or_staff_required
def projects_list(request):
    """List all projects with search and pagination"""
    search_query = request.GET.get('search', '')
    projects = Project.objects.all()
    
    if search_query:
        projects = projects.filter(
            models.Q(name__icontains=search_query) |
            models.Q(address__icontains=search_query) |
            models.Q(aliases__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(projects, 20)  # Show 20 projects per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "projects.html", {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_projects': projects.count()
    })

@login_required
@require_http_methods(["POST"])
def create_project(request):
    """Create a new project"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        aliases = data.get('aliases', [])
        builders_fee = data.get('builders_fee')
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Project name is required'
            })
        
        # Check if project already exists
        if Project.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': f'Project "{name}" already exists'
            })
        
        project = Project.objects.create(
            name=name,
            address=address,
            aliases=aliases,
            builders_fee=builders_fee
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Project "{name}" created successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'address': project.address,
                'aliases': project.aliases,
                'builders_fee': float(project.builders_fee) if project.builders_fee else None,
                'usage_count': project.usage_count,
                'created_at': project.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating project: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_project(request, project_id):
    """Update an existing project"""
    try:
        project = get_object_or_404(Project, id=project_id)
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        aliases = data.get('aliases', [])
        builders_fee = data.get('builders_fee')
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Project name is required'
            })
        
        # Check if name conflicts with another project
        if name != project.name and Project.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': f'Project "{name}" already exists'
            })
        
        project.name = name
        project.address = address
        project.aliases = aliases
        project.builders_fee = builders_fee
        project.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Project "{name}" updated successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'address': project.address,
                'aliases': project.aliases,
                'builders_fee': float(project.builders_fee) if project.builders_fee else None,
                'usage_count': project.usage_count,
                'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating project: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_project(request, project_id):
    """Delete a project"""
    try:
        project = get_object_or_404(Project, id=project_id)
        project_name = project.name
        project.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Project "{project_name}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting project: {str(e)}'
        })

@login_required
@admin_or_staff_required
def vendors_list(request):
    """List all vendors with search and pagination"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    vendors = Vendor.objects.prefetch_related('classes').all()
    
    if search_query:
        vendors = vendors.filter(
            models.Q(name__icontains=search_query) |
            models.Q(aliases__icontains=search_query)
        )
    
    if category_filter:
        vendors = vendors.filter(category=category_filter)
    
    # Get unique categories for filter dropdown
    categories = Vendor.objects.values_list('category', flat=True).distinct().order_by('category')
    
    # Get all classes for assignment dropdown
    all_classes = Class.objects.filter(is_active=True).order_by('parent__name', 'name')
    
    # Convert vendors to JSON for JavaScript
    vendors_json = []
    for vendor in vendors:
        vendor_classes = []
        for class_obj in vendor.classes.all():
            vendor_classes.append({
                'id': class_obj.id,
                'name': class_obj.name,
                'full_name': class_obj.full_name,
                'color': class_obj.color,
                'parent_name': class_obj.parent.name if class_obj.parent else None
            })
        
        vendors_json.append({
            'id': vendor.id,
            'name': vendor.name,
            'category': vendor.category,
            'aliases': vendor.aliases,
            'usage_count': vendor.usage_count,
            'created_at': vendor.created_at.strftime('%b %d, %Y'),
            'last_used': vendor.last_used.strftime('%b %d, %Y') if vendor.last_used else 'Never',
            'classes': vendor_classes
        })
    
    # Convert classes to JSON for JavaScript
    classes_json = []
    for class_obj in all_classes:
        classes_json.append({
            'id': class_obj.id,
            'name': class_obj.name,
            'full_name': class_obj.full_name,
            'color': class_obj.color,
            'parent_id': class_obj.parent.id if class_obj.parent else None,
            'parent_name': class_obj.parent.name if class_obj.parent else None,
            'is_parent': class_obj.is_parent,
            'is_child': class_obj.is_child,
            'display_name': class_obj.display_name
        })
    
    # Pagination
    paginator = Paginator(vendors, 20)  # Show 20 vendors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "vendors.html", {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'total_vendors': vendors.count(),
        'vendors_json': json.dumps(vendors_json),
        'classes_json': json.dumps(classes_json)
    })

@login_required
@require_http_methods(["POST"])
def create_vendor(request):
    """Create a new vendor"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        category = data.get('category', 'Other').strip()
        aliases = data.get('aliases', [])
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Vendor name is required'
            })
        
        # Check if vendor already exists
        if Vendor.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': f'Vendor "{name}" already exists'
            })
        
        vendor = Vendor.objects.create(
            name=name,
            category=category,
            aliases=aliases
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Vendor "{name}" created successfully',
            'vendor': {
                'id': vendor.id,
                'name': vendor.name,
                'category': vendor.category,
                'aliases': vendor.aliases,
                'usage_count': vendor.usage_count,
                'created_at': vendor.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating vendor: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_vendor(request, vendor_id):
    """Update an existing vendor"""
    try:
        vendor = get_object_or_404(Vendor, id=vendor_id)
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        category = data.get('category', 'Other').strip()
        aliases = data.get('aliases', [])
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Vendor name is required'
            })
        
        # Check if name conflicts with another vendor
        if name != vendor.name and Vendor.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': f'Vendor "{name}" already exists'
            })
        
        vendor.name = name
        vendor.category = category
        vendor.aliases = aliases
        vendor.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Vendor "{name}" updated successfully',
            'vendor': {
                'id': vendor.id,
                'name': vendor.name,
                'category': vendor.category,
                'aliases': vendor.aliases,
                'usage_count': vendor.usage_count,
                'updated_at': vendor.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating vendor: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_vendor(request, vendor_id):
    """Delete a vendor"""
    try:
        vendor = get_object_or_404(Vendor, id=vendor_id)
        vendor_name = vendor.name
        vendor.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Vendor "{vendor_name}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting vendor: {str(e)}'
        })

@login_required
def autocomplete_projects(request):
    """API endpoint for project autocomplete suggestions"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    projects = Project.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(address__icontains=query) |
        models.Q(aliases__icontains=query)
    )[:10]  # Limit to 10 suggestions
    
    suggestions = []
    for project in projects:
        suggestions.append({
            'id': project.id,
            'name': project.name,
            'address': project.address,
            'aliases': project.aliases,
            'builders_fee': float(project.builders_fee) if project.builders_fee else None,
            'usage_count': project.usage_count
        })
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def autocomplete_vendors(request):
    """API endpoint for vendor autocomplete suggestions"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    vendors = Vendor.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(aliases__icontains=query)
    )[:10]  # Limit to 10 suggestions
    
    suggestions = []
    for vendor in vendors:
        suggestions.append({
            'id': vendor.id,
            'name': vendor.name,
            'category': vendor.category,
            'aliases': vendor.aliases,
            'usage_count': vendor.usage_count
        })
    
    return JsonResponse({'suggestions': suggestions})

@login_required
@admin_or_staff_required
def transactions_list(request):
    """Display list of transactions with simple search"""
    transactions = Transaction.objects.all()
    
    # Simple search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            models.Q(description__icontains=search_query) |
            models.Q(amount__icontains=search_query) |
            models.Q(card_holder__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(transactions, 25)  # 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'search_query': search_query,
        'total_count': Transaction.objects.count(),
    }
    
    return render(request, 'transactions.html', context)

@login_required
@require_http_methods(["POST"])
def create_transaction(request):
    """Create a new transaction"""
    try:
        data = json.loads(request.body)
        
        transaction = Transaction.objects.create(
            date=data.get('date'),
            amount=data.get('amount'),
            description=data.get('description', ''),
            transaction_type=data.get('transaction_type', 'CHARGE'),
            card_holder=data.get('card_holder', ''),
            due_date=data.get('due_date') if data.get('due_date') else None,
            status=data.get('status', 'UNMATCHED'),
            tags=data.get('tags', [])
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction created successfully',
            'transaction': {
                'id': transaction.id,
                'date': transaction.date.strftime('%m/%d/%Y'),
                'amount': transaction.amount_display,
                'description': transaction.description,
                'transaction_type': transaction.transaction_type,
                'card_holder': transaction.card_holder,
                'due_date': transaction.due_date.strftime('%m/%d/%Y') if transaction.due_date else '',
                'status': transaction.status,
                'tags': transaction.tags
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating transaction: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_transaction(request, transaction_id):
    """Update an existing transaction"""
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        data = json.loads(request.body)
        
        transaction.date = data.get('date', transaction.date)
        transaction.amount = data.get('amount', transaction.amount)
        transaction.description = data.get('description', transaction.description)
        transaction.transaction_type = data.get('transaction_type', transaction.transaction_type)
        transaction.card_holder = data.get('card_holder', transaction.card_holder)
        transaction.due_date = data.get('due_date') if data.get('due_date') else None
        transaction.status = data.get('status', transaction.status)
        transaction.tags = data.get('tags', transaction.tags)
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction updated successfully',
            'transaction': {
                'id': transaction.id,
                'date': transaction.date.strftime('%m/%d/%Y'),
                'amount': transaction.amount_display,
                'description': transaction.description,
                'transaction_type': transaction.transaction_type,
                'card_holder': transaction.card_holder,
                'due_date': transaction.due_date.strftime('%m/%d/%Y') if transaction.due_date else '',
                'status': transaction.status,
                'tags': transaction.tags
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating transaction: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_transaction(request, transaction_id):
    """Delete a transaction"""
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        transaction.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting transaction: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def clear_all_transactions(request):
    """Clear all transactions"""
    try:
        count = Transaction.objects.count()
        Transaction.objects.all().delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {count} transactions'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error clearing transactions: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def clear_all_matches(request):
    """Clear all matched transactions"""
    try:
        count = Transaction.objects.filter(status='MATCHED').count()
        Transaction.objects.filter(status='MATCHED').delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {count} matched transactions'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error clearing matched transactions: {str(e)}'
        })

@login_required
def upload_csv_transactions(request):
    """Upload and process CSV file from QuickBooks"""
    print(f"Upload CSV view called. Method: {request.method}")
    print(f"Request.FILES: {request.FILES}")
    print(f"Request.POST: {request.POST}")
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST method allowed'
        })
    
    try:
        if 'csv_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No CSV file provided'
            })
        
        csv_file = request.FILES['csv_file']
        print(f"CSV file received: {csv_file.name}, size: {csv_file.size}")
        
        # Check file extension
        if not csv_file.name.lower().endswith('.csv'):
            return JsonResponse({
                'success': False,
                'message': 'Please upload a valid CSV file'
            })
        
        # Read and process CSV
        decoded_file = csv_file.read().decode('utf-8-sig')  # Handle BOM
        csv_reader = csv.DictReader(decoded_file.splitlines())
        
        # Debug: Print CSV headers to see what columns we have
        print(f"CSV Headers: {csv_reader.fieldnames}")
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Debug: Print row data
                print(f"Row {row_num}: {row}")
                
                # Map CSV columns to our model fields
                # Handle the specific format: Date, DESCRIPTION, Payee, Categorize or match, SPENT, RECEIVED
                # Try different possible column names (including BOM variants)
                date_str = (row.get('Date') or row.get('\ufeffDate') or row.get('date', '')).strip()
                description = row.get('DESCRIPTION', row.get('description', '')).strip()
                payee = row.get('Payee', row.get('payee', '')).strip()
                category = row.get('Categorize or match', row.get('category', '')).strip()
                spent_str = row.get('SPENT', row.get('spent', '')).strip()
                received_str = row.get('RECEIVED', row.get('received', '')).strip()
                
                print(f"Row {row_num} mapped values: date='{date_str}', description='{description}', spent='{spent_str}', received='{received_str}'")
                
                # Skip empty rows
                if not date_str or not description:
                    print(f"Row {row_num} skipped: missing date or description")
                    continue
                
                # Determine amount and transaction type from SPENT/RECEIVED columns
                amount = None
                transaction_type = 'CHARGE'
                
                if spent_str and spent_str != '':
                    # This is a SPENT transaction (expense/charge)
                    amount_str = spent_str
                    transaction_type = 'CHARGE'
                elif received_str and received_str != '':
                    # This is a RECEIVED transaction (income/credit)
                    amount_str = received_str
                    transaction_type = 'CREDIT'
                else:
                    # Skip rows with no amount
                    continue
                
                # Parse date (try multiple formats including MM/DD/YY)
                date_obj = None
                for date_format in ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, date_format).date()
                        break
                    except ValueError:
                        continue
                
                if not date_obj:
                    errors.append(f"Row {row_num}: Invalid date format '{date_str}'")
                    continue
                
                # Parse amount
                try:
                    # Remove currency symbols and commas
                    amount_clean = amount_str.replace('$', '').replace(',', '').strip()
                    amount = Decimal(amount_clean)
                except (ValueError, TypeError):
                    errors.append(f"Row {row_num}: Invalid amount format '{amount_str}'")
                    continue
                
                # Validate transaction type
                valid_types = ['CHARGE', 'CREDIT', 'PAYMENT', 'REFUND']
                if transaction_type not in valid_types:
                    transaction_type = 'CHARGE'  # Default to CHARGE
                
                # Create transaction
                print(f"Creating transaction: date={date_obj}, amount={amount}, description={description}, type={transaction_type}")
                transaction = Transaction.objects.create(
                    date=date_obj,
                    amount=amount,
                    description=description,
                    transaction_type=transaction_type,
                    card_holder=payee or 'Unknown',
                    status='UNMATCHED',
                    tags=[category] if category else []
                )
                
                imported_count += 1
                print(f"Transaction created successfully: {transaction.id}")
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        # Prepare response message
        print(f"Import complete: {imported_count} transactions imported, {len(errors)} errors")
        if imported_count > 0:
            message = f"Successfully imported {imported_count} transactions"
            if errors:
                message += f". {len(errors)} rows had errors."
        else:
            message = "No transactions were imported. Please check your CSV format."
        
        response_data = {
            'success': True,
            'message': message,
            'imported_count': imported_count,
            'errors': errors[:10]  # Limit errors to first 10
        }
        print(f"Response: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing CSV file: {str(e)}'
        })

@login_required
@admin_or_staff_required
def bills_list(request):
    """Display bills page with file list and bill entry tool"""
    files = File.objects.filter(
        project__isnull=False,
        vendor__isnull=False,
        invoice_number__isnull=False,
        total__isnull=False,
        approval_status='approved'  # Only show approved files
    ).exclude(project='', vendor='', invoice_number='', total='$0.00').order_by('-uploaded_at')
    
    # Convert files to JSON for JavaScript
    files_json = []
    for file in files:
        # Get attached transaction info
        attached_transaction = None
        if file.attached_transaction:
            attached_transaction = {
                'id': file.attached_transaction.id,
                'date': file.attached_transaction.date.strftime('%m/%d/%Y'),
                'amount': file.attached_transaction.amount_display,
                'description': file.attached_transaction.description,
                'card_holder': file.attached_transaction.card_holder,
                'status': file.attached_transaction.status
            }
        
        # Get class information
        class_info = None
        if file.selected_class:
            class_info = {
                'id': file.selected_class.id,
                'name': file.selected_class.name,
                'color': file.selected_class.color
            }
        
        files_json.append({
            'id': file.id,
            'name': file.name,
            'file_type': file.file_type,
            'file_size_display': file.file_size_display,
            'uploaded_at': file.uploaded_at.strftime('%b %d, %Y'),
            'description': file.description or '',
            'file': file.file.name if file.file else '',
            'project': file.project or '',
            'vendor': file.vendor or '',
            'date': file.date or '',
            'invoice_number': file.invoice_number or '',
            'total': file.total or '$0.00',
            'is_paid': file.is_paid,
            'payment_method': file.payment_method or '',
            'paid_at': file.paid_at.strftime('%b %d, %Y') if file.paid_at else '',
            'attached_transaction': attached_transaction,
            'selected_class': class_info
        })
    
    return render(request, "bills.html", {
        "files": files,
        "files_json": json.dumps(files_json)
    })

@login_required
@require_http_methods(["POST"])
def get_matching_transactions(request):
    """Get transactions that match the file amount"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        
        if not file_id:
            return JsonResponse({
                'success': False,
                'message': 'No file selected'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        
        # Extract amount from file total
        total_str = file_obj.total.replace('$', '').replace(',', '').strip()
        try:
            file_amount = Decimal(total_str)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid amount in file'
            })
        
        # Find transactions with matching amount (within $0.01 tolerance)
        tolerance = Decimal('0.01')
        matching_transactions = Transaction.objects.filter(
            amount__gte=file_amount - tolerance,
            amount__lte=file_amount + tolerance
        ).order_by('-date')
        
        transactions_data = []
        for transaction in matching_transactions:
            # Try to extract card number from description and find matching user
            user_name = None
            if transaction.description:
                # Look for 4-digit numbers in the description
                import re
                card_matches = re.findall(r'\b\d{4}\b', transaction.description)
                for card_match in card_matches:
                    user = get_user_by_card_number(card_match)
                    if user:
                        user_name = user.get_full_name() or user.username
                        break
            
            # Get attached file info if transaction is matched
            attached_file_info = None
            if transaction.status == 'MATCHED':
                attached_files = transaction.attached_files.all()
                if attached_files.exists():
                    attached_file = attached_files.first()
                    attached_file_info = {
                        'id': attached_file.id,
                        'name': attached_file.name,
                        'project': attached_file.project,
                        'vendor': attached_file.vendor,
                        'invoice_number': attached_file.invoice_number
                    }
            
            transactions_data.append({
                'id': transaction.id,
                'date': transaction.date.strftime('%m/%d/%Y'),
                'amount': transaction.amount_display,
                'description': transaction.description,
                'transaction_type': transaction.transaction_type,
                'card_holder': user_name or transaction.card_holder,  # Use actual user name if found, fallback to transaction card_holder
                'status': transaction.status,
                'user_name': user_name,
                'attached_file': attached_file_info
            })
        
        return JsonResponse({
            'success': True,
            'transactions': transactions_data,
            'file_amount': f"${file_amount:,.2f}"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting matching transactions: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def unmatch_transaction(request):
    """Unmatch a transaction from a file"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        transaction_id = data.get('transaction_id')
        
        if not file_id or not transaction_id:
            return JsonResponse({
                'success': False,
                'message': 'File ID and Transaction ID are required'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        transaction = get_object_or_404(Transaction, id=transaction_id)
        
        # Verify the transaction is actually attached to this file
        if file_obj.attached_transaction != transaction:
            return JsonResponse({
                'success': False,
                'message': 'Transaction is not attached to this file'
            })
        
        # Unmatch the transaction
        file_obj.attached_transaction = None
        file_obj.save()
        
        # Update transaction status back to UNMATCHED
        transaction.status = 'UNMATCHED'
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction unmatched successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error unmatching transaction: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def create_bill(request):
    """Create a bill entry for QuickBooks preparation"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        transaction_id = data.get('transaction_id')
        payment_method = data.get('payment_method', 'check')  # 'check' or 'credit_card'
        mark_as_paid = data.get('mark_as_paid', False)
        
        if not file_id:
            return JsonResponse({
                'success': False,
                'message': 'No file selected'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        
        # Generate bill number
        bill_number = generate_bill_number(file_obj.invoice_number, file_obj.project)
        
        # If transaction is matched, update its status and attach to file
        if transaction_id:
            transaction = get_object_or_404(Transaction, id=transaction_id)
            transaction.status = 'MATCHED'
            transaction.save()
            
            # Attach transaction to file
            file_obj.attached_transaction = transaction
            file_obj.save()
        
        # Mark file as paid if requested
        if mark_as_paid:
            from django.utils import timezone
            file_obj.is_paid = True
            file_obj.payment_method = payment_method
            file_obj.paid_at = timezone.now()
            file_obj.save()
            message = f'Bill marked as paid: {bill_number}'
        else:
            message = f'Bill created successfully: {bill_number}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'bill_number': bill_number,
            'payment_method': payment_method,
            'mark_as_paid': mark_as_paid,
            'file_info': {
                'vendor': file_obj.vendor,
                'project': file_obj.project,
                'amount': file_obj.total,
                'invoice_number': file_obj.invoice_number
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating bill: {str(e)}'
        })

def generate_bill_number(invoice_number, project_name):
    """Generate bill number from invoice number and project address"""
    # Find project by name to get address
    try:
        project = Project.objects.get(name=project_name)
        address = project.address
    except Project.DoesNotExist:
        address = project_name  # Fallback to project name if not found
    
    # Clean address - remove directional indicators (N, S, E, W, NE, NW, SE, SW)
    import re
    
    # Split address into words and remove directional indicators
    words = address.split()
    cleaned_words = []
    
    for word in words:
        # Remove common directional indicators (case insensitive)
        if word.upper() not in ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'NORTHEAST', 'NORTHWEST', 'SOUTHEAST', 'SOUTHWEST']:
            cleaned_words.append(word)
    
    # Join the cleaned words
    cleaned_address = ' '.join(cleaned_words)
    
    # Clean up extra spaces
    cleaned_address = ' '.join(cleaned_address.split())
    
    # Create bill number: invoice_number - address
    bill_number = f"{invoice_number} - {cleaned_address}"
    
    return bill_number

@login_required
@admin_or_staff_required
def users_list(request):
    """Display users page with card number management (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('username')
    
    # Get or create user profiles
    user_profiles = []
    for user in users:
        profile, created = UserProfile.objects.get_or_create(user=user)
        user_profiles.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            'card_number': profile.card_number or '',
            'profile_id': profile.id,
            'primary_role': profile.primary_role,
            'all_roles': profile.all_roles
        })
    
    # Get all available groups
    available_groups = Group.objects.all().order_by('name')
    
    return render(request, "users.html", {
        "user_profiles": user_profiles,
        "available_groups": available_groups
    })

@login_required
@require_http_methods(["POST"])
def update_user_card(request):
    """Update user's card number (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        card_number = data.get('card_number', '').strip()
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'No user selected'
            })
        
        user = get_object_or_404(User, id=user_id)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Validate card number if provided
        if card_number:
            if not card_number.isdigit() or len(card_number) != 4:
                return JsonResponse({
                    'success': False,
                    'message': 'Card number must be exactly 4 digits'
                })
        
        profile.card_number = card_number if card_number else None
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Card number updated for {user.get_full_name() or user.username}',
            'card_number': profile.card_number or ''
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating card number: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def create_user(request):
    """Create a new user (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        password = data.get('password', '').strip()
        is_staff = data.get('is_staff', False)
        is_active = data.get('is_active', True)
        group_ids = data.get('group_ids', [])
        
        # Validation
        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Username is required'
            })
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            })
        
        if not password:
            return JsonResponse({
                'success': False,
                'message': 'Password is required'
            })
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            })
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists'
            })
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_active=is_active
        )
        
        # Assign groups
        if group_ids:
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating user: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_user_groups(request):
    """Update user's groups/roles (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        group_ids = data.get('group_ids', [])
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'No user selected'
            })
        
        user = get_object_or_404(User, id=user_id)
        
        # Clear existing groups
        user.groups.clear()
        
        # Add new groups
        if group_ids:
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)
        
        # Get updated group names
        group_names = [group.name for group in user.groups.all()]
        
        return JsonResponse({
            'success': True,
            'message': f'Groups updated for {user.get_full_name() or user.username}',
            'group_names': group_names
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating groups: {str(e)}'
        })

@login_required
def get_project_superintendents(request, project_id):
    """Get superintendents for a project (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Get all superintendents
        superintendent_group = Group.objects.get(name='Superintendent')
        all_superintendents = User.objects.filter(groups=superintendent_group)
        
        # Get assigned superintendents for this project
        assigned_superintendents = project.superintendents.all()
        assigned_ids = set(assigned_superintendents.values_list('id', flat=True))
        
        superintendents_data = []
        for super in all_superintendents:
            superintendents_data.append({
                'id': super.id,
                'name': super.get_full_name() or super.username,
                'assigned': super.id in assigned_ids
            })
        
        return JsonResponse({
            'success': True,
            'superintendents': superintendents_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading superintendents: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def assign_project_superintendents(request, project_id):
    """Assign superintendents to a project (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        superintendent_ids = data.get('superintendent_ids', [])
        
        project = get_object_or_404(Project, id=project_id)
        
        # Get superintendents
        superintendent_group = Group.objects.get(name='Superintendent')
        superintendents = User.objects.filter(
            id__in=superintendent_ids,
            groups=superintendent_group
        )
        
        # Assign superintendents to project
        project.superintendents.set(superintendents)
        
        return JsonResponse({
            'success': True,
            'message': f'Superintendents assigned to {project.name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error assigning superintendents: {str(e)}'
        })

@login_required
def approvals_list(request):
    """Display approvals page with files that need approval"""
    # Get files that the user has access to based on their role and project assignments
    # Only show files that are pending approval
    files = File.objects.filter(
        project__isnull=False,
        vendor__isnull=False,
        invoice_number__isnull=False,
        total__isnull=False,
        approval_status='pending'  # Only show files pending approval
    ).exclude(project='', vendor='', invoice_number='', total='$0.00')
    
    # Filter files based on user access
    accessible_files = []
    
    # Check if user is admin/staff (full access)
    if request.user.is_staff:
        accessible_files = list(files)
        print(f"DEBUG: Admin user {request.user.username} - showing all {len(accessible_files)} files")
    else:
        # For non-admin users, check project assignments
        for file in files:
            has_access = False
            
            # Check if user is assigned to the project as superintendent
            if file.project and file.project.strip():
                try:
                    # Try exact match first
                    project = Project.objects.get(name=file.project)
                    if request.user in project.superintendents.all():
                        has_access = True
                        print(f"DEBUG: User {request.user.username} has access to project '{file.project}' (exact match)")
                except Project.DoesNotExist:
                    # Try case-insensitive match
                    try:
                        project = Project.objects.get(name__iexact=file.project)
                        if request.user in project.superintendents.all():
                            has_access = True
                            print(f"DEBUG: User {request.user.username} has access to project '{file.project}' (case-insensitive match)")
                    except Project.DoesNotExist:
                        # Try partial match with aliases
                        try:
                            project = Project.objects.filter(
                                models.Q(name__icontains=file.project) |
                                models.Q(aliases__icontains=file.project)
                            ).first()
                            if project and request.user in project.superintendents.all():
                                has_access = True
                                print(f"DEBUG: User {request.user.username} has access to project '{file.project}' (alias match)")
                        except:
                            pass
                
                if not has_access:
                    print(f"DEBUG: User {request.user.username} NO ACCESS to project '{file.project}'")
            
            if has_access:
                accessible_files.append(file)
    
    # Convert files to JSON for JavaScript
    print(f"DEBUG: Found {len(accessible_files)} accessible files")
    files_json = []
    for file in accessible_files:
        # Get attached transaction info
        attached_transaction = None
        if file.attached_transaction:
            attached_transaction = {
                'id': file.attached_transaction.id,
                'date': file.attached_transaction.date.strftime('%m/%d/%Y'),
                'amount': file.attached_transaction.amount_display,
                'description': file.attached_transaction.description,
                'card_holder': file.attached_transaction.card_holder,
                'status': file.attached_transaction.status
            }
        
        file_data = {
            'id': file.id,
            'name': file.name,
            'file_type': file.file_type,
            'file_size_display': file.file_size_display,
            'uploaded_at': file.uploaded_at.strftime('%b %d, %Y'),
            'description': file.description or '',
            'file': file.file.name if file.file else '',
            'project': file.project or '',
            'vendor': file.vendor or '',
            'date': file.date or '',
            'invoice_number': file.invoice_number or '',
            'total': file.total or '$0.00',
            'is_paid': file.is_paid,
            'payment_method': file.payment_method or '',
            'paid_at': file.paid_at.strftime('%b %d, %Y') if file.paid_at else '',
            'attached_transaction': attached_transaction,
            'approval_status': file.approval_status,
            'approval_comment': file.approval_comment or '',
            'approved_by': file.approved_by.get_full_name() if file.approved_by else '',
            'approved_at': file.approved_at.strftime('%b %d, %Y %I:%M %p') if file.approved_at else ''
        }
        print(f"DEBUG: Adding file {file.id}: {file.name}")
        files_json.append(file_data)
    
    # Get user's assigned projects for debugging
    user_projects = []
    if not request.user.is_staff:
        user_projects = Project.objects.filter(superintendents=request.user).values_list('name', flat=True)
        print(f"DEBUG: User {request.user.username} is assigned to projects: {list(user_projects)}")
    
    # Get all classes for selection
    all_classes = Class.objects.filter(is_active=True).order_by('parent__name', 'name')
    classes_json = []
    for class_obj in all_classes:
        classes_json.append({
            'id': class_obj.id,
            'name': class_obj.name,
            'full_name': class_obj.full_name,
            'color': class_obj.color,
            'parent_id': class_obj.parent.id if class_obj.parent else None,
            'parent_name': class_obj.parent.name if class_obj.parent else None,
            'is_parent': class_obj.is_parent,
            'is_child': class_obj.is_child,
            'display_name': class_obj.display_name
        })
    
    return render(request, "approvals.html", {
        "pending_files": accessible_files,  # Changed from "files" to "pending_files"
        "files_json": json.dumps(files_json),
        "user_projects": list(user_projects),
        "is_admin": request.user.is_staff,
        "classes_json": json.dumps(classes_json)
    })

@login_required
@require_http_methods(["POST"])
def update_file_approval(request):
    """Update file approval status"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        approval_status = data.get('approval_status')
        approval_comment = data.get('approval_comment', '')
        selected_class_id = data.get('selected_class_id')
        
        
        if not file_id or not approval_status:
            return JsonResponse({
                'success': False,
                'message': 'File ID and approval status are required'
            })
        
        # Class selection is required for all approval actions
        if not selected_class_id:
            return JsonResponse({
                'success': False,
                'message': 'Class selection is required for all approval actions'
            })
        
        # Comment is required for hold/reject actions
        if approval_status in ['on_hold', 'rejected'] and not approval_comment:
            return JsonResponse({
                'success': False,
                'message': 'Comment is required for Hold/Reject actions'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        
        # Check if user has access to this file
        has_access = False
        if request.user.is_staff:
            has_access = True
        elif hasattr(file_obj, 'project') and file_obj.project:
            try:
                project = Project.objects.get(name=file_obj.project)
                if request.user in project.superintendents.all():
                    has_access = True
            except Project.DoesNotExist:
                pass
        
        if not has_access:
            return JsonResponse({
                'success': False,
                'message': 'Access denied. You do not have permission to approve this file.'
            })
        
        # Update approval status
        file_obj.approval_status = approval_status
        file_obj.approval_comment = approval_comment
        file_obj.approved_by = request.user
        file_obj.approved_at = timezone.now()
        
        # Set selected class if provided
        if selected_class_id:
            try:
                # Convert to integer in case it comes as string
                class_id = int(selected_class_id)
                selected_class = Class.objects.get(id=class_id)
                file_obj.selected_class = selected_class
            except (Class.DoesNotExist, ValueError, TypeError) as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid class selected'
                })
        
        file_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': f'File approval status updated to {approval_status}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating approval status: {str(e)}'
        })

def get_user_by_card_number(card_number):
    """Helper function to get user by card number"""
    if not card_number or len(card_number) != 4:
        return None
    
    try:
        profile = UserProfile.objects.get(card_number=card_number)
        return profile.user
    except UserProfile.DoesNotExist:
        return None

@login_required
@require_http_methods(["POST"])
def delete_user(request):
    """Delete a user (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required.'
            })
        
        # Prevent deleting yourself
        if user_id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot delete your own account.'
            })
        
        user = get_object_or_404(User, id=user_id)
        username = user.username
        
        # Protect superuser from deletion
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete superuser account.'
            })
        
        # Delete the user (this will cascade to related objects)
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} has been deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting user: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def impersonate_user(request):
    """Impersonate a user (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required.'
            })
        
        # Prevent impersonating yourself
        if user_id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot impersonate yourself.'
            })
        
        user = get_object_or_404(User, id=user_id)
        
        # Store the original admin user ID in session for later restoration
        request.session['impersonated_by'] = request.user.id
        request.session['impersonated_user_id'] = user.id
        
        # Log in as the impersonated user
        from django.contrib.auth import login
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': f'Now impersonating {user.username}',
            'redirect_url': '/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error impersonating user: {str(e)}'
        })

@login_required
def stop_impersonation(request):
    """Stop impersonation and return to admin user"""
    if 'impersonated_by' not in request.session:
        return JsonResponse({
            'success': False,
            'message': 'No active impersonation session.'
        })
    
    try:
        admin_user_id = request.session['impersonated_by']
        admin_user = get_object_or_404(User, id=admin_user_id)
        
        # Log back in as the admin user
        from django.contrib.auth import login
        login(request, admin_user)
        
        # Clear impersonation session data
        del request.session['impersonated_by']
        del request.session['impersonated_user_id']
        
        return JsonResponse({
            'success': True,
            'message': f'Stopped impersonation. Back to {admin_user.username}',
            'redirect_url': '/users/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error stopping impersonation: {str(e)}'
        })

@login_required
@admin_or_staff_required
def classes_list(request):
    """Display classes page with CRUD functionality"""
    search_query = request.GET.get('search', '')
    classes = Class.objects.all()
    
    if search_query:
        classes = classes.filter(name__icontains=search_query)
    
    # Convert classes to JSON for JavaScript with hierarchical structure
    classes_json = []
    for class_obj in classes:
        classes_json.append({
            'id': class_obj.id,
            'name': class_obj.name,
            'description': class_obj.description,
            'color': class_obj.color,
            'is_active': class_obj.is_active,
            'vendor_count': class_obj.vendor_count,
            'created_at': class_obj.created_at.strftime('%b %d, %Y'),
            'updated_at': class_obj.updated_at.strftime('%b %d, %Y'),
            'parent_id': class_obj.parent.id if class_obj.parent else None,
            'parent_name': class_obj.parent.name if class_obj.parent else None,
            'is_parent': class_obj.is_parent,
            'is_child': class_obj.is_child,
            'full_name': class_obj.full_name,
            'display_name': class_obj.display_name,
            'children_count': class_obj.children.count() if class_obj.is_parent else 0
        })
    
    return render(request, "classes.html", {
        "classes": classes,
        "classes_json": json.dumps(classes_json),
        "search_query": search_query
    })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def create_class(request):
    """Create a new class"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        color = data.get('color', '#3B82F6').strip()
        parent_id = data.get('parent_id')
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Class name is required.'
            })
        
        # Check if class with this name already exists
        if Class.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': f'A class with the name "{name}" already exists.'
            })
        
        # Get parent if specified
        parent = None
        if parent_id:
            try:
                parent = Class.objects.get(id=parent_id)
            except Class.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid parent class selected.'
                })
        
        # Create the class
        class_obj = Class.objects.create(
            name=name,
            description=description,
            color=color,
            parent=parent
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Class "{name}" created successfully.',
            'class_id': class_obj.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating class: {str(e)}'
        })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def update_class(request):
    """Update an existing class"""
    try:
        data = json.loads(request.body)
        class_id = data.get('class_id')
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        color = data.get('color', '#3B82F6').strip()
        is_active = data.get('is_active', True)
        parent_id = data.get('parent_id')
        
        if not class_id:
            return JsonResponse({
                'success': False,
                'message': 'Class ID is required.'
            })
        
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Class name is required.'
            })
        
        class_obj = get_object_or_404(Class, id=class_id)
        
        # Check if another class with this name already exists
        if Class.objects.filter(name=name).exclude(id=class_id).exists():
            return JsonResponse({
                'success': False,
                'message': f'A class with the name "{name}" already exists.'
            })
        
        # Get parent if specified
        parent = None
        if parent_id:
            try:
                parent = Class.objects.get(id=parent_id)
                # Prevent setting self as parent
                if parent.id == class_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'A class cannot be its own parent.'
                    })
            except Class.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid parent class selected.'
                })
        
        # Update the class
        class_obj.name = name
        class_obj.description = description
        class_obj.color = color
        class_obj.is_active = is_active
        class_obj.parent = parent
        class_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Class "{name}" updated successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating class: {str(e)}'
        })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def delete_class(request):
    """Delete a class"""
    try:
        data = json.loads(request.body)
        class_id = data.get('class_id')
        
        if not class_id:
            return JsonResponse({
                'success': False,
                'message': 'Class ID is required.'
            })
        
        class_obj = get_object_or_404(Class, id=class_id)
        class_name = class_obj.name
        
        # Check if class is being used by vendors
        if class_obj.vendors.exists():
            return JsonResponse({
                'success': False,
                'message': f'Cannot delete class "{class_name}" because it is assigned to {class_obj.vendors.count()} vendor(s).'
            })
        
        # Check if class is being used by files
        if class_obj.assigned_files.exists():
            return JsonResponse({
                'success': False,
                'message': f'Cannot delete class "{class_name}" because it is assigned to {class_obj.assigned_files.count()} file(s).'
            })
        
        class_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Class "{class_name}" deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting class: {str(e)}'
        })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def update_vendor_classes(request):
    """Update vendor class assignments"""
    try:
        data = json.loads(request.body)
        vendor_id = data.get('vendor_id')
        class_ids = data.get('class_ids', [])
        
        if not vendor_id:
            return JsonResponse({
                'success': False,
                'message': 'Vendor ID is required.'
            })
        
        vendor = get_object_or_404(Vendor, id=vendor_id)
        
        # Clear existing class assignments
        vendor.classes.clear()
        
        # Add new class assignments
        for class_id in class_ids:
            try:
                class_obj = Class.objects.get(id=class_id)
                vendor.classes.add(class_obj)
            except Class.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Classes updated for {vendor.name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating vendor classes: {str(e)}'
        })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def change_user_password(request):
    """Change a user's password (admin only)"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not user_id or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'User ID and new password are required.'
            })
        
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long.'
            })
        
        user = get_object_or_404(User, id=user_id)
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Password updated successfully for {user.username}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error changing password: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def toggle_user_status(request):
    """Toggle user active status (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        })
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required.'
            })
        
        # Prevent deactivating yourself
        if user_id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot deactivate your own account.'
            })
        
        user = get_object_or_404(User, id=user_id)
        
        # Protect superuser from deactivation
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Cannot deactivate superuser account.'
            })
        
        # Toggle the user's active status
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} has been {status} successfully.',
            'is_active': user.is_active
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error toggling user status: {str(e)}'
        })

@login_required
@admin_or_staff_required
@require_http_methods(["POST"])
def send_back_for_review(request):
    """Send an approved bill back for review (change status from approved to pending)"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        
        if not file_id:
            return JsonResponse({
                'success': False,
                'message': 'File ID is required'
            })
        
        file_obj = get_object_or_404(File, id=file_id)
        
        # Check if the file is currently approved
        if file_obj.approval_status != 'approved':
            return JsonResponse({
                'success': False,
                'message': 'Only approved files can be sent back for review'
            })
        
        # Change status from approved to pending
        file_obj.approval_status = 'pending'
        file_obj.approval_comment = f'Sent back for review by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        file_obj.approved_by = None  # Clear the previous approver
        file_obj.approved_at = None  # Clear the approval timestamp
        file_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Bill sent back for review successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending bill back for review: {str(e)}'
        })

@login_required
@admin_or_staff_required
def settings_list(request):
    """Display settings page"""
    from django.utils import timezone
    
    # Get basic statistics
    user_count = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    current_time = timezone.now().strftime('%B %d, %Y at %I:%M %p')
    
    return render(request, "settings.html", {
        'user': request.user,
        'user_count': user_count,
        'active_users': active_users,
        'current_time': current_time
    })