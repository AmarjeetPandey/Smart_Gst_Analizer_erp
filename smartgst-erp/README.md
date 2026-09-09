# SmartGST AI ERP

**Production-Ready SaaS Platform for GST Management, Accounting, and Business Intelligence**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Node](https://img.shields.io/badge/node-16+-blue)
![React](https://img.shields.io/badge/react-18.2+-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)

## Overview

SmartGST AI ERP is a comprehensive, self-hostable SaaS application designed for shops, traders, wholesalers, distributors, accountants, GST consultants, and companies. It automates GST management, accounting, inventory, and business operations from a single centralized dashboard.

### Core Features

#### 🔐 Authentication System
- **Email OTP Authentication** - Secure passwordless login
- **JWT-based Session Management** - Multiple device support
- **Super Admin System** - Complete platform administration
- **Role-Based Access Control** - 6 user roles with granular permissions

#### 📄 AI Document Processing
- **Smart OCR** - Extract data from invoices, bills, receipts, GST documents
- **Auto-Detection** - Identify document type automatically
- **Duplicate Detection** - Flag duplicate invoices
- **Invoice Validation** - Auto-validate extracted data

#### 💰 GST Management
- **Sales Register** - Automatic tracking of all sales
- **Purchase Register** - Automatic tracking of all purchases
- **GSTR Reports** - Generate compliance reports
- **GST Ledger** - Complete GST transaction history
- **Tax Calculations** - Auto CGST/SGST/IGST calculations
- **ITC Tracking** - Input Tax Credit management

#### 📊 Accounting Module
- **Ledger Management** - Chart of accounts
- **Journal Entries** - Comprehensive journaling
- **Cash Book** - Cash transactions
- **Bank Book** - Bank reconciliation
- **Trial Balance** - Financial verification
- **P&L Statement** - Profit & Loss analysis
- **Balance Sheet** - Financial position

#### 📦 Inventory Management
- **Product Management** - SKU and barcode support
- **Stock Tracking** - Real-time inventory levels
- **Low Stock Alerts** - Automatic reorder notifications
- **Demand Forecasting** - ML-based predictions
- **Multi-warehouse** - Support for multiple locations

#### 👥 Customer & Vendor Management
- **Customer Database** - Complete customer profiles
- **Payment Tracking** - Outstanding receivables
- **Vendor Management** - Vendor payment history
- **Due Reminders** - Automated payment reminders
- **Payment Tracking** - Complete payment history

#### 🤖 AI Business Assistant
- **Natural Language Queries** - Ask business questions
- **Instant Reports** - Real-time analytics
- **Recommendations** - AI-powered insights
- **Trend Analysis** - Predictive analytics

#### 📈 Advanced Reporting
- **PDF Reports** - Downloadable reports
- **Excel Export** - Spreadsheet compatibility
- **Custom Dashboards** - Visual analytics
- **Charts & Graphs** - Trend visualization

#### 🏢 Multi-Branch Support
- **Multiple Locations** - Manage shops, branches, warehouses
- **Branch Reporting** - Branch-wise analytics
- **Centralized Control** - Master account oversight
- **Independent Tracking** - Per-branch inventory and GST

## Technology Stack

### Frontend
- **React 18.2** - Modern UI framework
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Query** - Server state management
- **Zustand** - Client state management
- **React Hook Form** - Form handling

### Backend
- **FastAPI** - High-performance Python framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Enterprise database
- **Redis** - Caching and queues
- **Celery** - Async task processing
- **Pydantic** - Data validation

### Machine Learning
- **TensorFlow** - Deep learning models
- **Scikit-learn** - Traditional ML models
- **Pytesseract** - OCR processing
- **OpenCV** - Image processing
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing

## Project Structure

```
smartgst-erp/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── api/routes/        # API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── core/              # Configuration & security
│   │   ├── middleware/        # Custom middleware
│   │   └── utils/             # Helper functions
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Unit tests
│   ├── requirements.txt       # Dependencies
│   └── main.py               # Entry point
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page views
│   │   ├── services/          # API services
│   │   ├── context/           # React Context
│   │   ├── hooks/             # Custom hooks
│   │   ├── styles/            # CSS/Tailwind
│   │   └── utils/             # Utilities
│   ├── public/                # Static assets
│   ├── index.html             # HTML entry
│   ├── package.json           # Dependencies
│   └── vite.config.js         # Vite config
│
├── ml-models/                  # ML Models
│   ├── sales_forecasting/     # Sales forecast model
│   ├── demand_prediction/     # Demand prediction
│   ├── fraud_detection/       # Fraud detection
│   ├── customer_segmentation/ # Customer clustering
│   └── ocr_processor/         # Document OCR
│
├── docker/                     # Docker setup
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   ├── DATABASE.md            # Database schema
│   ├── DEPLOYMENT.md          # Deployment guide
│   └── ML_MODELS.md           # ML models guide
│
├── SETUP_GUIDE.md             # Installation guide
├── README.md                  # This file
└── .env.example               # Environment template
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Clone and navigate to project**
   ```bash
   cd smartgst-erp
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   cp ../.env.example .env
   # Edit .env with your configuration
   uvicorn app.main:app --reload
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed instructions.

## Database Tables

### Core Tables
- **users** - User accounts and authentication
- **otp** - Email verification
- **user_sessions** - Multi-device session management
- **branches** - Shop/warehouse locations
- **customers** - Customer records
- **vendors** - Vendor records
- **products** - Product catalog
- **inventory** - Stock levels per product per branch

### Transaction Tables
- **invoices** - Sales invoices
- **invoice_items** - Line items
- **purchases** - Purchase orders
- **purchase_items** - Purchase line items
- **payments** - Customer payments
- **vendor_payments** - Vendor payments

### Financial Tables
- **ledgers** - Chart of accounts
- **transactions** - Ledger entries
- **gst_records** - GST tracking
- **audit_logs** - Activity audit trail

## API Endpoints

### Authentication
- `POST /api/v1/auth/send-otp` - Send OTP to email
- `POST /api/v1/auth/verify-otp` - Verify OTP and login
- `POST /api/v1/auth/refresh-token` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/activity` - Get activity history

### Branches
- `GET /api/v1/branches` - List branches
- `POST /api/v1/branches` - Create branch
- `GET /api/v1/branches/{id}` - Get branch details
- `PUT /api/v1/branches/{id}` - Update branch
- `DELETE /api/v1/branches/{id}` - Delete branch

### Invoices
- `GET /api/v1/invoices` - List invoices
- `POST /api/v1/invoices` - Create invoice
- `GET /api/v1/invoices/{id}` - Get invoice details
- `PUT /api/v1/invoices/{id}` - Update invoice
- `POST /api/v1/invoices/{id}/duplicate-check` - Check for duplicates

### Reports
- `GET /api/v1/reports/gstr-1` - GST Sales report
- `GET /api/v1/reports/gstr-2` - GST Purchase report
- `GET /api/v1/reports/profit-loss` - P&L statement
- `GET /api/v1/reports/balance-sheet` - Balance sheet

See [docs/API.md](./docs/API.md) for complete API documentation.

## Security Features

✅ **Email OTP Authentication** - No passwords needed
✅ **JWT Tokens** - Secure session management
✅ **HTTPS Support** - Encrypted communications
✅ **CORS Protection** - Cross-origin restrictions
✅ **Rate Limiting** - DDoS protection
✅ **SQL Injection Prevention** - SQLAlchemy ORM
✅ **XSS Protection** - React escaping
✅ **CSRF Protection** - Token verification
✅ **Audit Logging** - Complete audit trail
✅ **Data Encryption** - Sensitive field encryption
✅ **Role-Based Access** - Permission system
✅ **Multi-device Logout** - Session management

## Configuration

Required environment variables in `.env`:

```
# Database
DATABASE_URL=postgresql://user:pass@localhost/smartgst_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Gmail SMTP)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Admin
SUPER_ADMIN_EMAIL=admin@smartgst.com

# App Settings
ENVIRONMENT=production
DEBUG=False
```

See `.env.example` for all available options.

## Deployment

### Docker
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Manual Deployment
1. Setup Python virtual environment
2. Install dependencies
3. Configure PostgreSQL and Redis
4. Run database migrations
5. Setup SMTP service
6. Run FastAPI backend
7. Build React frontend
8. Configure web server (nginx/Apache)

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment.

## Development

### Code Structure
- **Services** - Business logic separation
- **Schemas** - Data validation with Pydantic
- **Models** - Database models with SQLAlchemy
- **Routes** - RESTful API endpoints
- **Middleware** - Request/response processing

### Testing
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

### Code Quality
- Type hints throughout
- Docstrings for all functions
- Configuration management
- Error handling
- Logging

## Performance

- **FastAPI**: 10,000+ requests/second
- **React**: Optimized for fast rendering
- **Redis**: Sub-millisecond caching
- **Database**: Indexed queries
- **ML Models**: Real-time predictions

## Scalability

- Horizontal scaling with load balancer
- Database replication support
- Redis cluster support
- Async task processing with Celery
- Microservices ready architecture

## Feature Roadmap

### Phase 1 (Current)
- ✅ Authentication system
- ✅ Basic invoice management
- ✅ Customer management
- ✅ GST tracking
- ✅ Accounting basics

### Phase 2
- Advanced reports
- Multi-branch analytics
- AI insights
- Mobile app

### Phase 3
- Advanced ML models
- Integration APIs
- Custom workflows
- White-label option

## Known Limitations

- ML models need training data for accuracy
- OCR works best with clear documents
- Real-time sync limited to poll interval
- No offline mode (future version)

## Support & Documentation

- **Setup Guide**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **API Docs**: [docs/API.md](./docs/API.md)
- **Database**: [docs/DATABASE.md](./docs/DATABASE.md)
- **Deployment**: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)
- **ML Models**: [docs/ML_MODELS.md](./docs/ML_MODELS.md)

## License

SmartGST AI ERP - Proprietary License
All Rights Reserved © 2024

## Contributing

This is a production ERP platform. For contributions:
1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Thorough testing required

## Disclaimer

This software is provided as-is. Users are responsible for:
- Data backup and recovery
- Security configuration
- Compliance with local laws
- GST compliance verification
- Regular updates and maintenance

## Version Info

- **Current Version**: 1.0.0
- **Last Updated**: 2024
- **Status**: Production Ready

---

**Get Started**: Read [SETUP_GUIDE.md](./SETUP_GUIDE.md) for installation instructions.

**Need Help?** Check the documentation folder or review API docs at http://localhost:8000/api/docs
