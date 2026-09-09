# 🎯 SmartGST AI ERP - QUICK TEST GUIDE

## ⚡ 60-Second Test

### Backend Running? ✅
```
Check: http://localhost:8000/health
Expected: {"status": "healthy", "app": "SmartGST AI ERP"}
```

### Frontend Running? ✅
```
Check: http://localhost:3000
Expected: SmartGST AI ERP login page
```

---

## 🔐 FULL LOGIN FLOW TEST (2 minutes)

### Step 1: Open Frontend
```
Browser: http://localhost:3000
You see: Beautiful login page with email input
```

### Step 2: Enter Email
```
Input: test@example.com
Click: "Send OTP" button
Status: Loading... then success message
```

### Step 3: Get OTP from Backend Terminal
```
Look at backend terminal output
Find: [DEV MODE] OTP for test@example.com: 123456
Copy: The 6-digit code (e.g., 123456)
```

### Step 4: Enter OTP
```
Input: Paste the 6-digit OTP
Click: "Verify OTP" button
Status: Loading... then redirects to dashboard
```

### Step 5: See Dashboard
```
You see: Dashboard with stats cards
- Total Sales: ₹0.00
- Outstanding: ₹0.00
- Inventory: 0
- Tax Due: ₹0.00
Click: "Logout" button (top right)
```

### Step 6: Back to Login
```
After logout: Redirected to login page again
Try: Login with different email
Success: Works perfectly!
```

---

## 📡 API TESTING (Interactive)

### Method 1: Swagger UI
```
Open: http://localhost:8000/api/docs
You see: Interactive API documentation
1. Expand: POST /api/v1/auth/send-otp
2. Click: "Try it out"
3. Enter: {"email": "api-test@example.com"}
4. Click: "Execute"
5. See: Response with message and email
6. Expand: POST /api/v1/auth/verify-otp
7. Copy OTP from step 5 response
8. Click: "Try it out"
9. Enter: {"email": "api-test@example.com", "code": "123456"}
10. Click: "Execute"
11. See: access_token, refresh_token, user data
```

### Method 2: Command Line
```bash
# Send OTP
curl -X POST "http://localhost:8000/api/v1/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Verify OTP (replace 123456 with actual OTP)
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'
```

---

## ✅ VERIFICATION CHECKLIST

After testing, you should have:

- [x] Backend server running (http://localhost:8000)
- [x] Frontend app running (http://localhost:3000)
- [x] Login page displaying correctly
- [x] OTP generation working
- [x] OTP verification working
- [x] Dashboard accessible after login
- [x] Logout working
- [x] API documentation available
- [x] Database created and populated
- [x] Tokens working properly

---

## 🚨 TROUBLESHOOTING

### Frontend Shows Blank Page
```
Fix 1: Hard refresh browser (Ctrl+Shift+R)
Fix 2: Check console (F12) for errors
Fix 3: Make sure http://localhost:3000 is in address bar
```

### Login Button Not Responding
```
Fix 1: Check backend is running
  → http://localhost:8000/health should return JSON
Fix 2: Check network tab in browser (F12)
  → POST to http://localhost:8000/api/v1/auth/send-otp
Fix 3: Check backend terminal for errors
```

### OTP Not Appearing
```
Fix 1: Check backend terminal for [DEV MODE] message
Fix 2: Scroll up in terminal to find OTP code
Fix 3: Try different email address
```

### CORS Errors
```
Fix 1: Should be fixed already
If still getting errors:
  → Check .env for CORS_ORIGINS
  → Restart backend server
  → Clear browser cache
```

---

## 🎓 WHAT'S HAPPENING BEHIND SCENES

### When You Enter Email:
```
1. Frontend sends: POST /api/v1/auth/send-otp {email: "..."}
2. Backend:
   a. Generates random 6-digit OTP
   b. Creates user if not exists
   c. Stores OTP in database
   d. Tries to send email (would work with SMTP setup)
   e. Returns response with status
3. Frontend shows: "OTP sent to your email"
4. Backend terminal shows: [DEV MODE] OTP: 123456
```

### When You Enter OTP:
```
1. Frontend sends: POST /api/v1/auth/verify-otp {email, code}
2. Backend:
   a. Finds OTP record
   b. Verifies code matches
   c. Checks OTP not expired
   d. Marks OTP as used
   e. Updates user record
   f. Generates JWT tokens
   g. Returns tokens + user data
3. Frontend:
   a. Stores tokens in cookies
   b. Saves user data
   c. Redirects to /dashboard
4. You see: Dashboard!
```

---

## 🎉 SUCCESS!

If you've followed all steps and everything works, your SmartGST AI ERP is:
- ✅ **Running** - Both servers active
- ✅ **Connected** - Frontend-Backend communicating
- ✅ **Authenticated** - OTP login working
- ✅ **Secured** - JWT tokens active
- ✅ **Database** - 38 tables ready
- ✅ **Documented** - Full API docs available

You're ready to **start implementing features!** 🚀

---

## 📊 NEXT FEATURES TO BUILD

Priority 1 (This Week):
1. Create invoice management endpoints
2. Add customer CRUD operations
3. Build product management
4. Implement payment recording
5. Add GST tracking

Priority 2 (Next Week):
1. Create dashboard components
2. Add reporting pages
3. Implement file uploads
4. Build advanced filters
5. Add notifications

Check [ROADMAP.md](./ROADMAP.md) for complete roadmap.

---

Happy testing! 🎊

For any issues, check [RUN_GUIDE.md](./RUN_GUIDE.md) or [RUNNING_STATUS.md](./RUNNING_STATUS.md)
