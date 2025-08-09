#!/bin/bash

# Smart Renamer Cloud Deployment Script
# This script helps set up and deploy the cloud application

set -e

echo "🚀 Smart Renamer Cloud Deployment Script"
echo "========================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Wrangler CLI..."
    npm install -g wrangler
fi

# Check if user is logged in to Cloudflare
if ! wrangler whoami &> /dev/null; then
    echo "🔐 Please log in to Cloudflare:"
    wrangler login
fi

echo "✅ Prerequisites check passed!"

# Backend setup
echo ""
echo "🔧 Setting up backend..."

cd backend

echo "📦 Installing dependencies..."
npm install

echo "🗄️ Creating D1 database..."
DB_ID=$(wrangler d1 create smart-renamer-db --json | jq -r '.id')

echo "🪣 Creating R2 bucket..."
BUCKET_NAME="smart-renamer-storage"
wrangler r2 bucket create $BUCKET_NAME

echo "📝 Updating wrangler.toml with database ID: $DB_ID"
sed -i.bak "s/your-database-id-here/$DB_ID/g" wrangler.toml
sed -i.bak "s/your-dev-database-id-here/$DB_ID/g" wrangler.toml

echo "🚀 Deploying Worker..."
wrangler deploy

# Get the Worker URL
WORKER_URL=$(wrangler whoami --json | jq -r '.account.name')".smart-renamer-api.workers.dev"
echo "✅ Worker deployed at: https://$WORKER_URL"

cd ..

# Database setup
echo ""
echo "🗄️ Setting up database..."

echo "📊 Applying database schema..."
cd backend
wrangler d1 execute smart-renamer-db --file=../database/schema.sql
cd ..

# Frontend setup
echo ""
echo "🎨 Setting up frontend..."

cd frontend

echo "🔗 Updating API URL in app.js..."
sed -i.bak "s|https://smart-renamer-api.your-subdomain.workers.dev|https://$WORKER_URL|g" app.js

echo "🔗 Updating API URL in _redirects..."
sed -i.bak "s|smart-renamer-api.your-subdomain.workers.dev|$WORKER_URL|g" _redirects

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Push this code to a GitHub repository"
echo "2. Connect the repository to Cloudflare Pages"
echo "3. Set the build directory to 'frontend'"
echo "4. Set the build command to 'echo \"No build needed\"'"
echo "5. Set the publish directory to 'frontend'"
echo ""
echo "🌐 Your application will be available at:"
echo "   Frontend: https://your-pages-url.pages.dev"
echo "   API: https://$WORKER_URL"
echo ""
echo "🔧 To test locally:"
echo "   Backend: cd backend && wrangler dev"
echo "   Frontend: cd frontend && python -m http.server 8000"
echo ""
echo "📚 For more information, see README.md" 