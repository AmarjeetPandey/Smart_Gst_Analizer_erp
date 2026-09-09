# SmartGST AI ERP - Complete Setup Guide

## Project Overview

SmartGST AI ERP is a production-ready SaaS platform for GST management, accounting, and business intelligence. It combines a React frontend, Python FastAPI backend, PostgreSQL database, and ML models.

### Key Features

- **Email OTP Authentication** - Secure passwordless login
- **Super Admin System** - Complete platform management
- **AI Document Processing** - OCR for invoice/bill extraction
- **GST Management** - Automated GST calculations and reports
- **Accounting Module** - Complete accounting system
- **Inventory Management** - Stock tracking and ML predictions
- **Business Analytics** - AI-powered insights and forecasting
- **Multi-branch Support** - Manage multiple shops/branches
- **Comprehensive Reporting** - PDF/Excel exports

## Technology Stack

### Frontend
- React 18.2.0
- Tailwind CSS
- React Router
- Axios
- Zustand (State Management)
- React Query (Data Fetching)

### Backend
- Python 3.9+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL
- Redis
- Celery (Task Queue)

### Machine Learning
- TensorFlow
- Scikit-learn
- PyTorch (for advanced models)
- OpenCV (OCR)

## System Requirements

### Backend Requirements
- Python 3.9 or higher
- PostgreSQL 12 or higher
- Redis 6.0 or higher

### Frontend Requirements
- Node.js 16 or higher
- npm or yarn

## Directory Structure

```
smartgst-erp/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Custom middleware
│   │   ├── core/              # Core configuration
│   │   └── utils/             # Utility functions
│   ├── migrations/            # Alembic migrations
│   ├── tests/                 # Unit tests
│   ├── requirements.txt       # Python dependencies
│   └── main.py               # Entry point
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── context/           # React context
│   │   ├── styles/            # CSS files
│   │   ├── utils/             # Utilities
│   │   ├── App.jsx            # Main App component
│   │   └── main.jsx           # Entry point
│   ├── public/                # Static files
│   ├── package.json
│   └── vite.config.js
│
├── ml-models/                  # Machine Learning Models
│   ├── forecasting/           # Sales forecasting
│   ├── fraud_detection/       # Fraud detection model
│   ├── demand_prediction/     # Demand prediction
│   └── ocr_processor/         # OCR processing
│
├── docker/                     # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/                       # Documentation
│   ├── API.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   └── ML_MODELS.md
│
└── .env.example               # Environment variables template
```

## Installation Guide

### Step 1: Clone Repository

```bash
cd smartgst-erp
```

### Step 2: Backend Setup

#### 2.1 Create Python Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

```bash
# Copy example file
cp ../.env.example .env

# Edit .env and set your configurations
# Important: Set DATABASE_URL, SMTP credentials, SUPER_ADMIN_EMAIL
```

#### 2.4 Setup PostgreSQL Database

```bash
# Create database
createdb smartgst_db

# Run Alembic migrations (when available)
alembic upgrade head
```

#### 2.5 Run Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/api/docs`

### Step 3: Frontend Setup

#### 3.1 Install Node Dependencies

```bash
cd frontend
npm install
```

#### 3.2 Configure Environment Variables

Create `.env.local` file:

```
VITE_API_URL=http://localhost:8000/api/v1
```

#### 3.3 Run Frontend Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Step 4: Redis Setup

#### 4.1 Install Redis

**On Windows:** Download from https://github.com/microsoftarchive/redis/releases

**On macOS:**
```bash
brew install redis
```

**On Linux (Ubuntu):**
```bash
sudo apt-get install redis-server
```

#### 4.2 Start Redis

```bash
redis-server
```

Redis will run on `localhost:6379`

## Database Schema

### Key Tables

#### users
- User authentication and profile
- Roles: super_admin, admin, manager, accountant, operator, viewer

#### otp
- Email verification OTPs
- Auto-expire after configured time

#### branches
- Multiple shop/warehouse locations
- Independent inventory and GST tracking

#### customers & vendors
- Customer and vendor management
- Outstanding tracking

#### invoices & purchases
- Sales and purchase orders
- Automatic GST calculations

#### inventory
- Stock tracking per product per branch
- ML-based demand forecasting

#### gst_records
- GST ledger entries
- Sales and purchase tracking

#### ledgers & transactions
- Complete accounting system
- Journal entries and balance tracking

#### audit_logs
- Comprehensive audit trail
- User activity logging

See `docs/DATABASE.md` for complete schema details.

## API Documentation

### Authentication Endpoints

#### Send OTP
```
POST /api/v1/auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Verify OTP
```
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {...},
  "expires_in": 1800
}
```

#### Refresh Token
```
POST /api/v1/auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

All other endpoints require Bearer token authorization:
```
Authorization: Bearer {access_token}
```

See `docs/API.md` for complete API documentation.

## Configuration

### Environment Variables

Create `.env` file with required variables:

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smartgst_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMTP (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Admin
SUPER_ADMIN_EMAIL=admin@smartgst.com

# Application
ENVIRONMENT=production
DEBUG=False
```

## Security Considerations

1. **Never commit `.env` files** - Use `.env.example` template
2. **Change SECRET_KEY** - Generate strong random key in production
3. **Use environment variables** - Don't hardcode sensitive data
4. **Enable HTTPS** - Required in production
5. **Configure CORS** - Set appropriate origins
6. **Rate limiting** - Enabled by default
7. **SQL injection protection** - Using SQLAlchemy ORM
8. **CSRF protection** - Implement in production

## Development Workflow

### Backend Development

1. Make changes to code
2. Uvicorn auto-reloads on save
3. Check API documentation at `/api/docs`
4. Run tests: `pytest`

### Frontend Development

1. Make changes to React components
2. Vite hot-reloads automatically
3. Check browser console for errors
4. Test authentication flow

### Database Migrations

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

### Docker Deployment

```bash
# Build images
docker-compose build

# Run containers
docker-compose up -d

# Check logs
docker-compose logs -f
```

See `docs/DEPLOYMENT.md` for detailed deployment instructions.

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Setup Redis in production
- [ ] Configure SMTP/Email service
- [ ] Enable HTTPS
- [ ] Setup domain/DNS
- [ ] Configure CORS origins
- [ ] Setup monitoring/logging
- [ ] Configure backups
- [ ] Load testing
- [ ] Security audit

## Machine Learning Models

### Available Models

1. **Sales Forecasting** - Predict future sales trends
2. **Demand Prediction** - Forecast product demand
3. **Fraud Detection** - Identify suspicious transactions
4. **Customer Segmentation** - Segment customers by behavior
5. **Duplicate Detection** - Identify duplicate invoices

See `docs/ML_MODELS.md` for model documentation.

## Troubleshooting

### Backend Issues

**Port 8000 already in use**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :8000
kill -9 <PID>
```

**Database connection error**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Ensure database exists

**SMTP error**
- Check Gmail app password (not regular password)
- Enable "Less secure app access"
- Check SMTP_USERNAME and SMTP_PASSWORD

### Frontend Issues

**Node modules issue**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Port 3000 already in use**
```bash
# Set different port
npm run dev -- --port 3001
```

## Support & Documentation

- **API Documentation**: http://localhost:8000/api/docs
- **Database Schema**: See `docs/DATABASE.md`
- **Deployment Guide**: See `docs/DEPLOYMENT.md`
- **ML Models**: See `docs/ML_MODELS.md`

## License

SmartGST AI ERP - All Rights Reserved

## Contributing

This is a production ERP platform. For modifications and extensions:

1. Follow code structure conventions
2. Add tests for new features
3. Update documentation
4. Test thoroughly before deployment

## Support

For issues, questions, or deployment support:

1. Check documentation files
2. Review error logs
3. Check browser/terminal console
4. Verify environment configuration

---

**Last Updated**: 2024
**Version**: 1.0.0
