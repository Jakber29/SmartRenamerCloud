#!/usr/bin/env python3
"""
Storage monitoring script for SmartRenamerCloud
Run this script to monitor disk usage and file storage
"""

import os
import shutil
import subprocess
from pathlib import Path
from django.core.management import setup_environ
import sys

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import File

def get_disk_usage(path):
    """Get disk usage for a given path"""
    total, used, free = shutil.disk_usage(path)
    return {
        'total': total,
        'used': used,
        'free': free,
        'used_percent': (used / total) * 100
    }

def get_file_stats():
    """Get file statistics from database"""
    files = File.objects.all()
    total_files = files.count()
    total_size = sum(file.size for file in files if file.size)
    
    # Group by file type
    file_types = {}
    for file in files:
        ext = file.file_type or 'unknown'
        if ext not in file_types:
            file_types[ext] = {'count': 0, 'size': 0}
        file_types[ext]['count'] += 1
        file_types[ext]['size'] += file.size or 0
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'file_types': file_types
    }

def format_bytes(bytes_value):
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def main():
    print("📊 SmartRenamerCloud Storage Monitor")
    print("=" * 50)
    
    # Get current directory disk usage
    current_dir = Path.cwd()
    disk_usage = get_disk_usage(current_dir)
    
    print(f"💾 Disk Usage for {current_dir}:")
    print(f"   Total: {format_bytes(disk_usage['total'])}")
    print(f"   Used:  {format_bytes(disk_usage['used'])} ({disk_usage['used_percent']:.1f}%)")
    print(f"   Free:  {format_bytes(disk_usage['free'])}")
    
    # Check if we're in a Django project
    try:
        file_stats = get_file_stats()
        
        print(f"\n📁 File Statistics:")
        print(f"   Total Files: {file_stats['total_files']}")
        print(f"   Total Size:  {format_bytes(file_stats['total_size'])}")
        
        print(f"\n📄 Files by Type:")
        for ext, stats in sorted(file_stats['file_types'].items()):
            print(f"   {ext}: {stats['count']} files ({format_bytes(stats['size'])})")
        
        # Check media directory
        media_dir = current_dir / 'media'
        if media_dir.exists():
            media_usage = get_disk_usage(media_dir)
            print(f"\n📂 Media Directory Usage:")
            print(f"   Size: {format_bytes(media_usage['used'])}")
            
            # Check files subdirectory
            files_dir = media_dir / 'files'
            if files_dir.exists():
                files_usage = get_disk_usage(files_dir)
                print(f"   Files: {format_bytes(files_usage['used'])}")
        
        # Storage recommendations
        print(f"\n💡 Storage Recommendations:")
        if disk_usage['used_percent'] > 80:
            print("   ⚠️  WARNING: Disk usage is over 80%!")
            print("   Consider implementing cloud storage or cleaning up old files")
        elif disk_usage['used_percent'] > 60:
            print("   ⚡ Disk usage is getting high. Consider monitoring more closely")
        else:
            print("   ✅ Disk usage is healthy")
        
        if file_stats['total_size'] > 5 * 1024 * 1024 * 1024:  # 5GB
            print("   📦 Large file storage detected. Consider cloud storage for better performance")
        
    except Exception as e:
        print(f"   ⚠️  Could not get Django file stats: {e}")
        print("   Make sure you're running this from the Django project directory")
    
    print("\n" + "=" * 50)
    print("Run this script regularly to monitor storage usage")

if __name__ == "__main__":
    main()
