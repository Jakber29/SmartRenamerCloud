import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Import team members from team_members.json file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='team_members.json',
            help='Path to the team members JSON file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually creating users'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        # Read JSON file
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON file: {e}')
            )
            return
        
        team_members = data.get('team_members', [])
        if not team_members:
            self.stdout.write(
                self.style.WARNING('No team members found in file')
            )
            return
        
        # Title to Group mapping
        title_to_group = {
            'Owner': 'Superintendent',
            'Manager': 'Project Manager',
            'Project Manager': 'Project Manager',
            'Coordinator': 'Accounting',
            'Designer Assistant': 'Designer',
            'Technician': 'Designer',  # Field workers get designer access
            'Supervisor': 'Project Manager',
            'Superintendant': 'Superintendent',
            'Contractor': 'Designer',  # External contractors get limited access
        }
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write(f'Processing {len(team_members)} team members...')
        
        for member in team_members:
            name = member.get('name', '').strip()
            email = member.get('email', '').strip()
            card_last_four = member.get('card_last_four', '').strip()
            title = member.get('title', '').strip()
            
            if not name:
                self.stdout.write(
                    self.style.WARNING(f'Skipping member with no name: {member}')
                )
                skipped_count += 1
                continue
            
            # Generate username from name
            username = name.lower().replace(' ', '.').replace('/', '.')
            # Remove any special characters
            username = ''.join(c for c in username if c.isalnum() or c == '.')
            
            # Generate email if not provided
            if not email:
                email = f"{username}@davidelliot.la"
            
            # Determine group based on title
            group_name = title_to_group.get(title, 'Designer')  # Default to Designer
            
            if dry_run:
                self.stdout.write(
                    f'Would create: {name} ({username}) - {email} - Card: {card_last_four} - Group: {group_name}'
                )
                continue
            
            try:
                with transaction.atomic():
                    # Check if user already exists
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': name.split()[0] if name.split() else '',
                            'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                            'is_active': True,
                            'is_staff': title in ['Owner', 'Manager', 'Superintendant']
                        }
                    )
                    
                    if created:
                        # Set password (users will need to reset it)
                        user.set_password('temp_password_123')
                        user.save()
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created user: {name} ({username})')
                        )
                    else:
                        # Update existing user
                        user.email = email
                        user.first_name = name.split()[0] if name.split() else ''
                        user.last_name = ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                        user.is_staff = title in ['Owner', 'Manager', 'Superintendant']
                        user.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated user: {name} ({username})')
                        )
                    
                    # Get or create user profile
                    profile, profile_created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={'card_number': card_last_four}
                    )
                    
                    if not profile_created and card_last_four:
                        profile.card_number = card_last_four
                        profile.save()
                    
                    # Assign group
                    try:
                        group = Group.objects.get(name=group_name)
                        user.groups.clear()
                        user.groups.add(group)
                        self.stdout.write(f'  Assigned to group: {group_name}')
                    except Group.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'  Group not found: {group_name}')
                        )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {name}: {str(e)}')
                )
                skipped_count += 1
        
        if not dry_run:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS(f'Import completed!')
            )
            self.stdout.write(f'Created: {created_count} users')
            self.stdout.write(f'Updated: {updated_count} users')
            self.stdout.write(f'Skipped: {skipped_count} users')
            self.stdout.write('\nNote: All users have temporary password "temp_password_123"')
            self.stdout.write('Users should reset their passwords on first login.')
        else:
            self.stdout.write(f'\nDry run completed. Would process {len(team_members)} members.')
