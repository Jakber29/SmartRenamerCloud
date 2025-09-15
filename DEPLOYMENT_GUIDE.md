# 🚀 SmartRenamerCloud Deployment Guide

## 📊 Storage Analysis & Solutions

### Current Storage Setup
- **Files**: Stored in `media/files/` directory (local filesystem)
- **Database**: SQLite (`db.sqlite3`)
- **File Size**: No limits currently set

### Storage Concerns & Solutions

#### 🚨 **Shared Linode Storage Issues**
**Problem**: Limited disk space on shared hosting
- Typical shared Linode: 20-80GB total space
- 1000 PDF files: ~1-10GB storage needed
- Database + system files: ~2-5GB

**Solutions**:
1. **Cloud Storage** (Recommended): Use AWS S3, DigitalOcean Spaces, or Linode Object Storage
2. **Upgrade Linode**: Move to dedicated server with more storage
3. **File Compression**: Implement PDF compression
4. **File Cleanup**: Archive old files

#### 💾 **Recommended Storage Solutions**

##### Option 1: Linode Object Storage (Cheapest)
```bash
# Cost: $5/month for 250GB + $0.02/GB transfer
# Setup in production settings:
AWS_ACCESS_KEY_ID = your_linode_access_key
AWS_SECRET_ACCESS_KEY = your_linode_secret_key
AWS_STORAGE_BUCKET_NAME = your_bucket_name
AWS_S3_ENDPOINT_URL = 'https://us-southeast-1.linodeobjects.com'
```

##### Option 2: AWS S3 (Most Reliable)
```bash
# Cost: $0.023/GB/month + transfer costs
# Setup in production settings:
AWS_ACCESS_KEY_ID = your_aws_access_key
AWS_SECRET_ACCESS_KEY = your_aws_secret_key
AWS_STORAGE_BUCKET_NAME = your_bucket_name
```

##### Option 3: Local Storage with Monitoring
```bash
# Monitor disk usage
df -h
du -sh /var/www/smartrenamer/media/
```

## 🛠️ Deployment Requirements

### Server Requirements
- **RAM**: Minimum 1GB (2GB recommended)
- **Storage**: 20GB minimum (50GB+ recommended)
- **CPU**: 1 vCPU minimum
- **OS**: Ubuntu 20.04+ or CentOS 8+

### Software Requirements
- Python 3.8+
- PostgreSQL 12+
- Nginx
- Gunicorn
- Git

## 📋 Pre-Deployment Checklist

### 1. Prepare Your Code
- [ ] Test locally with production settings
- [ ] Update `ALLOWED_HOSTS` in production settings
- [ ] Set secure `SECRET_KEY`
- [ ] Configure database settings
- [ ] Set up environment variables

### 2. Server Preparation
- [ ] Create Linode server (Ubuntu 20.04+)
- [ ] Set up SSH access
- [ ] Configure firewall (ports 22, 80, 443)
- [ ] Update system packages

### 3. Domain & SSL
- [ ] Point domain to Linode IP
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure DNS records

## 🚀 Deployment Steps

### Step 1: Server Setup
```bash
# Connect to your Linode server
ssh root@your-linode-ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

### Step 2: Deploy Application
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

### Step 3: Configure Environment
```bash
# Edit environment file
nano /var/www/smartrenamer/.env

# Update with your actual values:
SECRET_KEY=your-super-secret-key-here
DB_PASSWORD=your_secure_password_here
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Step 4: Set Up Cloud Storage (Optional but Recommended)
```bash
# Install additional packages
pip install django-storages boto3

# Update production settings to use cloud storage
# Uncomment cloud storage configuration in settings_production.py
```

## 🔧 Post-Deployment Configuration

### 1. SSL Certificate
```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com
```

### 2. Firewall Configuration
```bash
# Configure UFW
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

### 3. Database Backup
```bash
# Create backup script
cat > /var/www/smartrenamer/backup.sh << EOF
#!/bin/bash
pg_dump -h localhost -U smartrenamer_user smartrenamer > /var/backups/smartrenamer_\$(date +%Y%m%d_%H%M%S).sql
find /var/backups -name "smartrenamer_*.sql" -mtime +7 -delete
EOF

chmod +x /var/www/smartrenamer/backup.sh

# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /var/www/smartrenamer/backup.sh
```

## 📊 Monitoring & Maintenance

### Disk Usage Monitoring
```bash
# Check disk usage
df -h

# Check media folder size
du -sh /var/www/smartrenamer/media/

# Set up alerts when disk usage > 80%
```

### Application Monitoring
```bash
# Check application status
systemctl status smartrenamer

# Check logs
tail -f /var/www/smartrenamer/logs/django.log

# Check Nginx logs
tail -f /var/log/nginx/error.log
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Out of Disk Space
```bash
# Check what's using space
du -sh /var/www/smartrenamer/media/*
du -sh /var/log/*

# Clean up old files
find /var/www/smartrenamer/media -type f -mtime +90 -delete
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check database connection
sudo -u postgres psql -c "SELECT 1;"
```

#### 3. Application Not Starting
```bash
# Check Gunicorn logs
journalctl -u smartrenamer -f

# Check application logs
tail -f /var/www/smartrenamer/logs/django.log
```

## 💰 Cost Estimation

### Linode Server Costs
- **Shared CPU 1GB**: $5/month
- **Shared CPU 2GB**: $10/month
- **Dedicated CPU 2GB**: $12/month

### Storage Costs
- **Local Storage**: Included with server
- **Linode Object Storage**: $5/month for 250GB
- **AWS S3**: ~$0.023/GB/month

### Total Monthly Cost
- **Basic Setup**: $5-10/month (server only)
- **With Cloud Storage**: $10-15/month
- **Production Setup**: $15-25/month

## 🔒 Security Considerations

1. **Environment Variables**: Never commit secrets to git
2. **Database Security**: Use strong passwords
3. **SSL Certificate**: Always use HTTPS in production
4. **Firewall**: Only open necessary ports
5. **Regular Updates**: Keep system and packages updated
6. **Backups**: Regular database and file backups

## 📞 Support

If you encounter issues during deployment:
1. Check the logs first
2. Verify all environment variables are set
3. Ensure all services are running
4. Check firewall and network settings
5. Review the troubleshooting section above
