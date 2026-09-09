# SmartGST AI ERP - Complete Running Guide

## ✅ BOTH SERVERS ARE NOW RUNNING!

### Backend Status
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### Frontend Status
- **URL**: http://localhost:3000
- **Status**: React Vite dev server running with HMR

---

## 🚀 Testing the Application

### Step 1: Open Frontend in Browser
1. Go to http://localhost:3000
2. You should see the SmartGST AI ERP login page

### Step 2: Test OTP Authentication
1. **Enter any email address** (e.g., `test@gmail.com`)
2. Click **"Send OTP"**
3. **Check the terminal output** - you'll see the OTP code displayed (e.g., `[DEV MODE] OTP for test@gmail.com: 123456`)
4. Copy that OTP and enter it in the frontend
5. Click **"Verify OTP"**
6. You'll be logged in and redirected to the Dashboard

### Step 3: Dashboard
- You should see the dashboard with stats cards
- Click **"Logout"** to test logout functionality
- Try logging in again with a different email

---

## 📊 API Testing

### Test Health Check
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{"status": "healthy", "app": "SmartGST AI ERP"}
```

### Test API Version
```bash
curl http://localhost:8000/api/v1
```
Expected response:
```json
{
  "app_name": "SmartGST AI ERP",
  "version": "1.0.0",
  "environment": "development"
}
```

### Interactive API Testing
Visit http://localhost:8000/api/docs and use the Swagger UI to:
1. Click on **POST /auth/send-otp**
2. Click "Try it out"
3. Enter an email: `{"email": "test@example.com"}`
4. Click "Execute"
5. Copy the OTP code from the response
6. Use **POST /auth/verify-otp** to verify it

---

## 🛠️ Features Ready to Use

### ✅ Working Features
1. **OTP-based Authentication**
   - Send OTP to email (Dev mode shows OTP in console)
   - Verify OTP
   - JWT token generation
   - Token refresh mechanism

2. **Protected Routes**
   - Dashboard is protected
   - Redirects to login if not authenticated
   - Session persistence

3. **API Integration**
   - Frontend connected to backend
   - Automatic token refresh on expiry
   - Proper CORS configuration

4. **Database**
   - SQLite database ready
   - All 38 tables created
   - User sessions tracked

---

## 📁 Project Structure

```
✓ Backend (Running on http://localhost:8000)
  ├── FastAPI application
  ├── SQLAlchemy ORM
  ├── SQLite database
  ├── Authentication system
  └── API endpoints ready

✓ Frontend (Running on http://localhost:3000)
  ├── React 18 application
  ├── Tailwind CSS styling
  ├── Hot Module Replacement
  ├── Login page with OTP
  └── Protected dashboard
```

---

## 🎯 Next Steps - What to Implement

### High Priority (Do First)
1. **Create Invoice Endpoints** - `POST /api/v1/invoices`, `GET /api/v1/invoices`, etc.
2. **Add Customer Management** - CRUD operations for customers
3. **Product Management** - CRUD for products/inventory
4. **Payment Recording** - Track payments from customers
5. **GST Tracking** - Calculate and track GST

### Medium Priority
1. **Dashboard Components** - Tables, charts, reports
2. **Inventory Management** - Stock tracking
3. **Report Generation** - PDF/Excel exports
4. **Notifications** - Payment reminders, low stock alerts

### Lower Priority
1. **ML Models** - Forecasting, fraud detection
2. **OCR Integration** - Document processing
3. **Advanced Analytics** - Business intelligence
4. **Third-party Integrations** - Bank, payment gateway

---

## 🔧 Troubleshooting

### Frontend shows blank page
- Check browser console (F12) for errors
- Make sure http://localhost:3000 is loading
- Clear browser cache and refresh

### Login not working
- **Backend not responding?** Check if http://localhost:8000/health returns `{"status": "healthy"}`
- **OTP not showing?** Check backend terminal for `[DEV MODE] OTP for...`
- **Token issues?** Clear cookies and try again

### Backend errors
- Check terminal output for error messages
- Verify `.env` file has correct settings
- Make sure SQLite database file is writable

### API documentation not loading
- Visit http://localhost:8000/api/docs
- If blank, check backend console for startup errors
- Try http://localhost:8000/api/redoc as alternative

---

## 📝 Development Tips

1. **Enable Frontend Hot Reload**
   - Save any file in `frontend/src/` and browser auto-refreshes
   - No need to restart dev server

2. **View OTP in Development**
   - Backend terminal shows OTP codes for testing
   - Look for `[DEV MODE] OTP for...` messages

3. **API Testing**
   - Use http://localhost:8000/api/docs (Swagger UI)
   - Try endpoints interactively
   - See request/response examples

4. **Database**
   - SQLite file at `backend/smartgst_dev.db`
   - Delete to reset database
   - Tables auto-create on startup

---

## 🚀 Production Readiness

This is a **fully working development setup**. For production:

1. **Database**: Switch to PostgreSQL
   - Update `DATABASE_URL` in `.env`
   - Install `psycopg2`

2. **Email**: Configure real SMTP
   - Add Gmail/SendGrid credentials
   - Enable production email sending

3. **Security**
   - Update `SECRET_KEY` to a random value
   - Set proper CORS origins
   - Enable HTTPS
   - Configure rate limiting

4. **Deployment**
   - Use Docker (Dockerfile already provided)
   - Deploy to AWS, GCP, or Azure
   - Setup CI/CD pipeline

---

## 📞 Support

### Documentation
- Main README: [README.md](./README.md)
- API Reference: [docs/API.md](./docs/API.md)
- Database Schema: [docs/DATABASE.md](./docs/DATABASE.md)
- Deployment Guide: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

### Quick Debug
1. Check backend terminal for logs
2. Check frontend browser console (F12)
3. Verify API responding: `curl http://localhost:8000/health`
4. Check database: Look for `smartgst_dev.db`

---

## ✨ You're All Set!

Both backend and frontend are **running properly** with:
- ✅ Full authentication working
- ✅ OTP generation in dev mode
- ✅ JWT tokens
- ✅ Protected routes
- ✅ API documentation
- ✅ Database ready

**Start building features!** 🎯

For questions, check the documentation files in the `/docs` folder.

Happy coding! 🚀
