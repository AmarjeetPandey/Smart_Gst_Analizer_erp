# SmartGST AI ERP - Quick Start Guide

## 5-Minute Setup

### Option A: Docker (Fastest)

```bash
# 1. Prerequisites installed? (Docker, Docker Compose)
# If not, install from https://www.docker.com/products/docker-desktop

# 2. Clone/extract project
cd smartgst-erp

# 3. Configure
cp .env.example .env
# Edit .env - at minimum set SMTP_USERNAME and SMTP_PASSWORD

# 4. Run
cd docker
docker-compose up -d

# 5. Access
# Frontend: http://localhost:3000
# API: http://localhost:8000/api/docs
```

**That's it!** The app will be running.

---

### Option B: Local (For Developers)

#### Backend
```bash
cd backend

# Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt

# Configure
cp ../.env.example .env
# Edit with your settings

# Run
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend

# Install
npm install

# Run
npm run dev
```

#### Requirements
- Python 3.9+
- Node.js 16+
- PostgreSQL running
- Redis running

---

## First Login

1. Go to http://localhost:3000
2. Enter your email
3. Click "Send OTP"
4. Check your email for OTP code
5. Enter OTP and login
6. Welcome to dashboard!

---

## Key Features to Explore

### 1. Create a Branch
```
Dashboard → Settings → Branches → Add Branch
```

### 2. Add Products
```
Dashboard → Inventory → Products → Add Product
```

### 3. Create Invoice
```
Dashboard → Invoices → New Invoice
- Select customer
- Add line items
- System auto-calculates GST
- Save
```

### 4. View Reports
```
Dashboard → Reports
- Sales Report
- GST Summary
- Profit & Loss
- Balance Sheet
```

### 5. AI Features
```
Dashboard → AI Assistant
- Ask: "What is my sales this month?"
- Ask: "Show pending payments"
- Ask: "Which customers are at risk?"
```

---

## Configuration Checklist

### Essential Settings (in .env)

```
✓ DATABASE_URL - Your PostgreSQL connection
✓ SMTP_USERNAME - Gmail address for OTP
✓ SMTP_PASSWORD - Gmail app password (not regular password)
✓ SUPER_ADMIN_EMAIL - Your email for admin access
✓ SECRET_KEY - Random secret key
```

### Optional But Recommended

```
ENVIRONMENT=production    # Set to production after testing
DEBUG=False              # Disable debug in production
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com"]
```

---

## Troubleshooting

### Docker Issues

**Containers won't start:**
```bash
docker-compose logs
# Check what error is shown
```

**Port already in use:**
```bash
# Change in docker-compose.yml
# ports:
#   - "8001:8000"  # Use different port
```

**Database connection error:**
```bash
# Check if PostgreSQL in docker-compose is healthy
docker ps
# All containers should show "healthy" status
```

### Local Setup Issues

**Module not found:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Database error:**
```bash
# Check PostgreSQL running
psql -U postgres

# Check connection string
echo $DATABASE_URL
```

**SMTP error:**
```bash
# Gmail requires app password (not regular password)
# Enable 2FA: https://myaccount.google.com/security
# Generate app password: https://myaccount.google.com/apppasswords
```

---

## Next Steps

1. **Read documentation**
   - [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Detailed setup
   - [API.md](./docs/API.md) - API reference
   - [DATABASE.md](./docs/DATABASE.md) - Database schema

2. **Explore features**
   - Create test data
   - Generate reports
   - Try AI assistant
   - Check invoice OCR

3. **Configure settings**
   - Add your branches
   - Setup customers/vendors
   - Add products
   - Configure GST settings

4. **Customize**
   - Update branding
   - Add company logo
   - Customize email templates
   - Configure notification rules

5. **Deploy**
   - Test thoroughly
   - Follow [DEPLOYMENT.md](./docs/DEPLOYMENT.md)
   - Setup production environment
   - Configure SSL/HTTPS
   - Setup backups

---

## Admin Features (Super Admin Only)

Access as: `admin@smartgst.com` (configured in .env)

```
Dashboard → Admin Panel
- Manage all users
- View platform analytics
- Configure system settings
- Manage SMTP settings
- Monitor storage usage
- View login history
- Export platform reports
```

---

## Common Tasks

### Add New Customer
1. Dashboard → Customers → Add
2. Enter name, phone, GST number
3. Set credit limit
4. Save

### Create Invoice
1. Dashboard → Invoices → New
2. Select customer and branch
3. Add products/items
4. GST auto-calculated
5. Preview and save

### Record Payment
1. Dashboard → Invoices → Find invoice
2. Click "Record Payment"
3. Enter amount and method
4. Save

### Generate Report
1. Dashboard → Reports
2. Select report type
3. Choose date range
4. View or export

### Check GST Summary
1. Dashboard → GST → Monthly Summary
2. Select month/year
3. View sales, purchases, tax
4. Generate GSTR report

---

## API Usage Example

```bash
# Send OTP
curl -X POST http://localhost:8000/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Login with OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}'

# Get user profile
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

See [API.md](./docs/API.md) for complete API documentation.

---

## System Requirements

### Minimum
- RAM: 4GB
- Storage: 20GB
- CPU: 2 cores

### Recommended
- RAM: 8GB
- Storage: 50GB+
- CPU: 4 cores

### For Production
- RAM: 16GB+
- Storage: 100GB+ (SSD)
- CPU: 8+ cores
- Load balancer
- Database replication
- Automated backups

---

## Support & Resources

- **API Documentation**: http://localhost:8000/api/docs (when running)
- **GitHub**: [Repository URL]
- **Issues**: [Issues page]
- **Documentation**: This folder

---

## What's Included

✅ Complete authentication system
✅ Invoice management
✅ Customer & vendor management
✅ GST tracking
✅ Accounting system
✅ Inventory management
✅ Financial reports
✅ AI document processing
✅ Multi-branch support
✅ Multi-device login
✅ Comprehensive audit logging
✅ Super admin system
✅ Production-ready code
✅ Docker support
✅ Complete documentation

---

## What's Next

After getting familiar with the application:

1. **Customize UI** - Update branding and colors
2. **Add integrations** - Bank feeds, market data
3. **Setup automation** - Scheduled reports, reminders
4. **Train ML models** - With your historical data
5. **Scale up** - Multi-server deployment

---

## Get Help

**Error on startup?**
1. Check logs: `docker-compose logs`
2. Check .env configuration
3. Ensure ports are free
4. Verify all services are healthy

**Feature not working?**
1. Check API docs
2. Review error messages
3. Check browser console (F12)
4. Check application logs

**Need customization?**
1. Review codebase structure
2. Check documentation
3. Modify code as needed
4. Test thoroughly before deploying

---

**Ready to go?** Start with: `cd docker && docker-compose up -d`

Then visit: http://localhost:3000

Enjoy SmartGST AI ERP! 🚀
