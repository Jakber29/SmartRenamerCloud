from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import File, Project, Vendor, Transaction, UserProfile


class Command(BaseCommand):
    help = 'Create user role groups and assign permissions'

    def handle(self, *args, **options):
        # Define the groups and their permissions
        groups_data = {
            'Accounting': {
                'description': 'Accounting staff with access to bills and transactions',
                'permissions': [
                    'view_file', 'add_file', 'change_file', 'delete_file',
                    'view_transaction', 'add_transaction', 'change_transaction', 'delete_transaction',
                    'view_userprofile', 'change_userprofile',
                ]
            },
            'Superintendent': {
                'description': 'Superintendent with full project oversight',
                'permissions': [
                    'view_file', 'add_file', 'change_file', 'delete_file',
                    'view_project', 'add_project', 'change_project', 'delete_project',
                    'view_vendor', 'add_vendor', 'change_vendor', 'delete_vendor',
                    'view_transaction', 'add_transaction', 'change_transaction', 'delete_transaction',
                    'view_userprofile', 'change_userprofile',
                ]
            },
            'Project Manager': {
                'description': 'Project Manager with project and vendor management',
                'permissions': [
                    'view_file', 'add_file', 'change_file',
                    'view_project', 'add_project', 'change_project',
                    'view_vendor', 'add_vendor', 'change_vendor',
                    'view_transaction', 'add_transaction', 'change_transaction',
                ]
            },
            'Designer': {
                'description': 'Designer with limited access to projects and files',
                'permissions': [
                    'view_file', 'add_file', 'change_file',
                    'view_project', 'view_vendor',
                ]
            }
        }

        # Create groups and assign permissions
        for group_name, group_info in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group already exists: {group_name}')
                )

            # Clear existing permissions
            group.permissions.clear()

            # Add permissions
            permissions_added = 0
            for perm_codename in group_info['permissions']:
                try:
                    # Try to find permission in core app first
                    permission = Permission.objects.get(
                        codename=perm_codename,
                        content_type__app_label='core'
                    )
                    group.permissions.add(permission)
                    permissions_added += 1
                except Permission.DoesNotExist:
                    # If not found in core, try auth app for user-related permissions
                    try:
                        permission = Permission.objects.get(
                            codename=perm_codename,
                            content_type__app_label='auth'
                        )
                        group.permissions.add(permission)
                        permissions_added += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'Permission not found: {perm_codename}')
                        )

            self.stdout.write(
                self.style.SUCCESS(f'Added {permissions_added} permissions to {group_name}')
            )

        self.stdout.write(
            self.style.SUCCESS('\nSuccessfully set up all user role groups!')
        )
