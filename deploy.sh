#!/bin/bash

# SmartRenamerCloud Deployment Script for Linode
# Run this script on your Linode server

echo "🚀 Starting SmartRenamerCloud deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git

# Create project directory
echo "📁 Setting up project directory..."
sudo mkdir -p /var/www/smartrenamer
sudo chown $USER:$USER /var/www/smartrenamer
cd /var/www/smartrenamer

# Clone or copy your project files here
# git clone https://github.com/yourusername/SmartRenamerCloud.git .

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Set up PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE DATABASE smartrenamer;
CREATE USER smartrenamer_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE smartrenamer TO smartrenamer_user;
\q
EOF

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
SECRET_KEY=your-super-secret-key-here
DEBUG=False
DB_NAME=smartrenamer
DB_USER=smartrenamer_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EOF

# Run Django migrations
echo "🔄 Running database migrations..."
python manage.py migrate --settings=config.settings_production

# Create superuser (optional)
echo "👤 Creating superuser..."
python manage.py createsuperuser --settings=config.settings_production

# Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings_production

# Create logs directory
mkdir -p logs

# Set up Gunicorn service
echo "🔧 Setting up Gunicorn service..."
sudo tee /etc/systemd/system/smartrenamer.service > /dev/null << EOF
[Unit]
Description=SmartRenamerCloud Gunicorn daemon
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/smartrenamer
Environment="PATH=/var/www/smartrenamer/venv/bin"
ExecStart=/var/www/smartrenamer/venv/bin/gunicorn --workers 3 --bind unix:/var/www/smartrenamer/smartrenamer.sock config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx configuration
echo "🌐 Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/smartrenamer > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com your-linode-ip;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/smartrenamer;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /var/www/smartrenamer;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/smartrenamer/smartrenamer.sock;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/smartrenamer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl start smartrenamer
sudo systemctl enable smartrenamer
sudo systemctl restart nginx

# Set proper permissions
sudo chown -R $USER:www-data /var/www/smartrenamer
sudo chmod -R 755 /var/www/smartrenamer

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: http://your-linode-ip"
echo "📝 Don't forget to:"
echo "   1. Update your domain DNS to point to your Linode IP"
echo "   2. Set up SSL certificate with Let's Encrypt"
echo "   3. Configure your firewall (ufw allow 80,443)"
echo "   4. Update the .env file with your actual credentials"
