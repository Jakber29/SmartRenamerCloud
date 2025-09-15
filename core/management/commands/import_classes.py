from django.core.management.base import BaseCommand
from django.db import transaction
import json
import os
from core.models import Class

class Command(BaseCommand):
    help = 'Import classes from classes.json file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='classes.json',
            help='Path to the classes JSON file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing classes before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File {file_path} not found')
            )
            return
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON file: {e}')
            )
            return
        
        with transaction.atomic():
            # Clear existing classes if requested
            if clear_existing:
                deleted_count = Class.objects.count()
                Class.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted {deleted_count} existing classes')
                )
            
            # Define colors for parent categories
            parent_colors = {
                'GENERAL SERVICES': '#3B82F6',  # Blue
                'SITE SERVICES': '#10B981',     # Green
                'FRAMING': '#F59E0B',           # Yellow
                'WINDOWS/EXTERIOR DOORS': '#8B5CF6',  # Purple
                'PLUMBING': '#06B6D4',          # Cyan
                'ELECTRICAL': '#F97316',        # Orange
                'UTILITY CO. FEES': '#84CC16',  # Lime
                'CONCRETE': '#6B7280',          # Gray
                'FIRE SAFETY': '#EF4444',       # Red
                'HVAC': '#14B8A6',              # Teal
                'FINISHES': '#EC4899',          # Pink
                'EXTERIOR SITE WORK': '#8B5A2B', # Brown
                'SPECIALTY': '#6366F1'          # Indigo
            }
            
            # Child color (slightly lighter than parent)
            child_color = '#E5E7EB'  # Light gray
            
            created_parents = 0
            created_children = 0
            
            # Create parent classes first
            for parent_name, children in data.items():
                # Create or get parent class
                parent_class, parent_created = Class.objects.get_or_create(
                    name=parent_name,
                    defaults={
                        'description': f'Parent category for {parent_name.lower()}',
                        'color': parent_colors.get(parent_name, '#3B82F6'),
                        'parent': None,
                        'is_active': True
                    }
                )
                
                if parent_created:
                    created_parents += 1
                    self.stdout.write(f'Created parent class: {parent_name}')
                else:
                    self.stdout.write(f'Parent class already exists: {parent_name}')
                
                # Create child classes
                for child_name in children:
                    child_class, child_created = Class.objects.get_or_create(
                        name=child_name,
                        defaults={
                            'description': f'Child class under {parent_name}',
                            'color': child_color,
                            'parent': parent_class,
                            'is_active': True
                        }
                    )
                    
                    if child_created:
                        created_children += 1
                        self.stdout.write(f'  Created child class: {child_name}')
                    else:
                        self.stdout.write(f'  Child class already exists: {child_name}')
            
            success_message = (
                f'Import completed successfully!\n'
                f'Created {created_parents} parent classes\n'
                f'Created {created_children} child classes\n'
                f'Total classes: {Class.objects.count()}'
            )
            
            self.stdout.write(self.style.SUCCESS(success_message))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing classes: {e}')
            )
            raise
