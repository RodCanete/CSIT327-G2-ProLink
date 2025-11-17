# PayMongo Integration - Setup Guide

## ✅ What's Been Integrated:

### 1. **PayMongo Service Layer** (`transactions/paymongo_service.py`)
- Checkout session creation
- Payment status verification
- Webhook handling
- Test mode support with dummy cards

### 2. **Payment Views** (`transactions/payment_views.py`)
- `initiate_payment` - Start PayMongo checkout
- `payment_success` - Handle successful payments
- `payment_cancel` - Handle cancelled payments
- `paymongo_webhook` - Receive PayMongo events
- `test_payment_info` - Show test credentials

### 3. **Updated Flow**
- Professional accepts → Request status becomes `'awaiting_payment'`
- Transaction created with `'pending_payment'`
- Professional redirected to messaging
- Client sees "Pay Now" button

### 4. **New Templates**
- `payment_cancel.html` - Payment cancelled page
- `test_payment_info.html` - Test credentials guide

---

## 🚀 Setup Instructions:

### Step 1: Install Dependencies
```bash
cd "C:\Users\Rod Gabrielle\Desktop\experimental PROLINK\prolink"
.\env\Scripts\Activate.ps1
pip install requests
```

### Step 2: Get PayMongo API Keys

1. **Sign up for PayMongo:**
   - Go to https://dashboard.paymongo.com/signup
   - Create an account
   - Verify your email

2. **Get Test API Keys:**
   - Go to Dashboard → Developers → API Keys
   - Copy your **Test Public Key** (starts with `pk_test_`)
   - Copy your **Test Secret Key** (starts with `sk_test_`)

3. **Add to Environment:**

Create/update `.env` file in `prolink/prolink/` directory:
```env
# PayMongo Test Keys
PAYMONGO_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY_HERE
PAYMONGO_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
```

**OR** add directly to `settings.py` (for testing only):
```python
PAYMONGO_PUBLIC_KEY = 'pk_test_YOUR_KEY_HERE'
PAYMONGO_SECRET_KEY = 'sk_test_YOUR_KEY_HERE'
```

### Step 3: Run Migration
```bash
python manage.py makemigrations requests
python manage.py migrate requests
```

### Step 4: Test the Flow!

---

## 🧪 Testing with Dummy Money:

### **Access Test Info Page:**
Visit: `http://127.0.0.1:8000/transactions/test-payment-info/`

This page shows all test credentials you can use!

### **Test Card Numbers:**

✅ **Successful Payment:**
- Card: `4343434343434345`
- CVC: `123`
- Expiry: `12/25`

❌ **Declined Payment:**
- Card: `4571736000000075`
- CVC: `123`
- Expiry: `12/25`

💳 **Insufficient Funds:**
- Card: `4571736000000067`
- CVC: `123`
- Expiry: `12/25`

### **Test GCash:**
- Use any phone number (e.g., `09123456789`)
- Payment will auto-succeed in test mode

---

## 📱 Complete User Flow:

### **1. Professional Side:**
```
Client creates request
    ↓
Professional sees in "Client Requests"
    ↓
Professional clicks "Respond to Request"
    ↓
Professional clicks "Accept" button
    ↓
Request status → 'awaiting_payment'
Transaction created
    ↓
Professional redirected to Messages
Can now chat with client
```

### **2. Client Side:**
```
Professional accepted request
    ↓
Client sees "Payment Required" notification
    ↓
Client clicks "Pay Now" button
    ↓
Redirected to PayMongo checkout page
    ↓
Choose payment method:
  - Credit/Debit Card
  - GCash
  - GrabPay
  - Maya (PayMaya)
    ↓
Enter test credentials
    ↓
Complete payment
    ↓
Redirected to success page
    ↓
Transaction status → 'escrowed'
Request status → 'in_progress'
    ↓
Professional can start work!
```

---

## 🔧 What Still Needs to be Done:

### **1. Add "Pay Now" Button to Client Dashboard**
Update `dashboard_client.html` to show payment button for `awaiting_payment` requests.

### **2. Add Notification System**
- Email client when professional accepts
- Show badge/notification on dashboard

### **3. Webhook URL Configuration**
- Once deployed, add webhook URL in PayMongo dashboard:
  `https://yourdomain.com/transactions/webhook/paymongo/`

### **4. Production Mode**
When ready for real payments:
- Get **Live API Keys** from PayMongo
- Update `.env` with `pk_live_` and `sk_live_` keys
- Test thoroughly before launching!

---

## 💰 PayMongo Pricing (Philippines):

- **Card payments:** 2.9% + ₱15 per transaction
- **GCash:** 2.0% per transaction
- **GrabPay:** 2.0% per transaction
- **Maya:** 2.0% per transaction
- **No monthly fees**
- **No setup fees**

**Example:** ₱1,000 payment
- Card: ₱1,000 × 2.9% + ₱15 = ₱44 fee
- GCash: ₱1,000 × 2.0% = ₱20 fee

---

## 🐛 Troubleshooting:

**Payment not working?**
1. Check API keys are correct
2. Make sure you're using **test** keys (pk_test_ / sk_test_)
3. Use only the test card numbers provided
4. Check browser console for errors

**Webhook not receiving events?**
- Webhooks only work on public URLs (not localhost)
- Use ngrok for local testing
- Or test manually without webhooks first

**"Unauthorized" error?**
- Double-check secret key
- Make sure key starts with `sk_test_`

---

## 📚 Resources:

- **PayMongo Docs:** https://developers.paymongo.com/
- **Test Cards:** https://developers.paymongo.com/docs/testing
- **Dashboard:** https://dashboard.paymongo.com/

---

## ✨ Next Steps:

1. **Install `requests` package**
2. **Add your PayMongo test keys**
3. **Run migrations**
4. **Visit test info page:** `/transactions/test-payment-info/`
5. **Create a test request and try the flow!**

Enjoy testing with dummy money! 🎉
