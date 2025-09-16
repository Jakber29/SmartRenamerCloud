#!/bin/bash

# SmartRenamerCloud Deployment Script
# This script deploys the latest code from GitHub to your Linode server

set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Configuration
REPO_URL="https://github.com/Jakber29/SmartRenamerCloud.git"
APP_DIR="/var/www/smartrenamer"
BACKUP_DIR="/var/backups/smartrenamer"
SERVICE_NAME="smartrenamer"  # Your systemd service name

# Create backup directory if it doesn't exist
sudo mkdir -p $BACKUP_DIR

# Create app directory if it doesn't exist
sudo mkdir -p $APP_DIR

# Backup current deployment
if [ -d "$APP_DIR" ] && [ "$(ls -A $APP_DIR)" ]; then
    echo "📦 Creating backup..."
    sudo cp -r $APP_DIR $BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S)
fi

# Clone or pull latest code
if [ -d "$APP_DIR/.git" ]; then
    echo "🔄 Pulling latest changes..."
    cd $APP_DIR
    sudo git pull origin main
else
    echo "📥 Cloning repository..."
    sudo git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

# Install/update dependencies
echo "📦 Installing dependencies..."
cd $APP_DIR
sudo -u www-data python3 -m pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
sudo -u www-data python3 manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
sudo -u www-data python3 manage.py collectstatic --noinput

# Restart the service
echo "🔄 Restarting service..."
sudo systemctl restart $SERVICE_NAME

# Check service status
echo "✅ Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "🎉 Deployment completed successfully!"
echo "🌐 Your app should be live at: http://your-linode-ip"