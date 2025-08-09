# Smart Renamer Cloud

A cloud-based version of the Smart Renamer application built with Cloudflare's free tier services.

## Architecture

This application uses Cloudflare's free tier services:

- **Cloudflare Pages**: Hosts the frontend (HTML/CSS/JS)
- **Cloudflare Workers**: Provides the backend API
- **Cloudflare D1**: Database for storing application data
- **Cloudflare R2**: Object storage for files (optional)

## Features

- **File Management**: Upload and manage files in the cloud
- **Transaction Matching**: Match uploaded files with CSV transaction data
- **Vendor Management**: Add, edit, and manage vendor information
- **Project Management**: Track projects and their details
- **Team Member Management**: Manage team members and their card information
- **Reimbursement Tracking**: Track reimbursement requests
- **Real-time Dashboard**: View system statistics and status

## Free Tier Limits

### Cloudflare Pages
- Unlimited requests
- 500 builds per month
- 100GB bandwidth per month

### Cloudflare Workers
- 100,000 requests per day
- 10ms CPU time per request
- 128MB memory per request

### Cloudflare D1
- 1 database
- 100MB storage
- 1,000 reads per day
- 1,000 writes per day

### Cloudflare R2
- 10GB storage
- 1,000,000 Class A operations per month
- 10,000,000 Class B operations per month

## Setup Instructions

### 1. Prerequisites

- Cloudflare account
- Node.js 18+ installed
- Wrangler CLI installed: `npm install -g wrangler`

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Login to Cloudflare:
   ```bash
   wrangler login
   ```

4. Create D1 database:
   ```bash
   wrangler d1 create smart-renamer-db
   ```

5. Create R2 bucket:
   ```bash
   wrangler r2 bucket create smart-renamer-storage
   ```

6. Update `wrangler.toml` with your database and bucket IDs

7. Deploy the Worker:
   ```bash
   wrangler deploy
   ```

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Update the API URL in `app.js`:
   ```javascript
   const API_BASE_URL = 'https://your-worker-url.workers.dev';
   ```

3. Deploy to Cloudflare Pages:
   - Connect your GitHub repository to Cloudflare Pages
   - Set the build directory to `frontend`
   - Set the build command to `echo "No build needed"`
   - Set the publish directory to `frontend`

### 4. Database Setup

1. Apply the database schema:
   ```bash
   wrangler d1 execute smart-renamer-db --file=../database/schema.sql
   ```

## Development

### Local Development

1. Start the Worker locally:
   ```bash
   cd backend
   wrangler dev
   ```

2. Serve the frontend locally:
   ```bash
   cd frontend
   python -m http.server 8000
   ```

3. Update the API URL in `app.js` to point to your local Worker

### Environment Variables

The following environment variables are used:

- `DB`: D1 database binding
- `STORAGE`: R2 bucket binding

## API Endpoints

### Vendors
- `GET /api/vendors` - Get all vendors
- `POST /api/vendors` - Create a new vendor

### Projects
- `GET /api/projects` - Get all projects
- `POST /api/projects` - Create a new project

### Team Members
- `GET /api/team-members` - Get all team members
- `POST /api/team-members` - Create a new team member

### Transactions
- `GET /api/transactions` - Get all transactions
- `POST /api/upload-csv` - Upload CSV data

### Manual Matches
- `GET /api/manual-matches` - Get manual matches
- `POST /api/manual-match` - Create a manual match

### Reimbursements
- `GET /api/reimbursements` - Get all reimbursements
- `POST /api/reimbursements` - Create a new reimbursement

### Transaction Tags
- `GET /api/transaction-tags` - Get transaction tags
- `POST /api/transaction-tags` - Save transaction tags

## File Structure

```
SmartRenamerCloud/
├── backend/                 # Cloudflare Worker backend
│   ├── src/
│   │   └── index.js        # Main Worker file
│   ├── package.json
│   └── wrangler.toml       # Worker configuration
├── frontend/               # Cloudflare Pages frontend
│   ├── index.html          # Main HTML file
│   ├── styles.css          # CSS styles
│   ├── app.js              # JavaScript application
│   ├── _headers            # Cloudflare Pages headers
│   └── _redirects          # Cloudflare Pages redirects
├── database/
│   └── schema.sql          # D1 database schema
└── README.md               # This file
```

## Security Considerations

- All API endpoints include CORS headers
- Content Security Policy is configured
- Input validation is implemented
- SQL injection protection through parameterized queries

## Performance

- Static assets are cached with long-term headers
- API responses are optimized for minimal payload
- Database queries are indexed for performance
- CDN distribution through Cloudflare's global network

## Monitoring

- Worker logs are available in the Cloudflare dashboard
- D1 database metrics are tracked
- R2 storage usage is monitored
- Pages analytics are available

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the API URL is correct in `app.js`
2. **Database Errors**: Check that the D1 database is created and schema is applied
3. **File Upload Issues**: Verify R2 bucket permissions
4. **Worker Deployment Failures**: Check `wrangler.toml` configuration

### Debug Mode

Enable debug logging in the Worker by adding:
```javascript
console.log('Debug info:', data);
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Cloudflare documentation
3. Open an issue on GitHub 