# 🔄 ProLink Complete User Flow
**Last Updated:** November 15, 2025

## **System Overview**
ProLink connects clients with professionals through a secure escrow payment system. This document outlines the complete user journey from request creation to completion, including edge cases.

---

## **📊 Status Reference Table**

### **Request Statuses**
| Status | Meaning | Who Can Act |
|--------|---------|-------------|
| `pending` | Awaiting professional acceptance OR awaiting client payment | Professional (accept/decline) OR Client (pay) |
| `in_progress` | Professional is working on the request | Professional (submit work) |
| `under_review` | Work submitted, awaiting client review | Client (approve/request revision) |
| `revision_requested` | Client requested changes | Professional (resubmit) |
| `completed` | Work approved, payment released | Both (leave review) |
| `disputed` | Dispute opened, under admin review | Admin only |
| `cancelled` | Request cancelled/refunded | None (terminal state) |
| `declined` | Professional declined the request | None (terminal state) |

### **Transaction Statuses**
| Status | Meaning | Money Location |
|--------|---------|----------------|
| `pending_payment` | Waiting for client to pay | None yet |
| `escrowed` | Payment received, held in escrow | ProLink escrow |
| `pending_approval` | Work submitted, awaiting approval | ProLink escrow |
| `completed` | Payment released to professional | Professional's account |
| `disputed` | Under dispute resolution | ProLink escrow (frozen) |
| `refunded` | Money returned to client | Client's account |
| `failed` | Payment processing failed | None |

---

## **🎬 COMPLETE USER FLOW**

---

## **PHASE 1: Request Creation & Professional Selection**

### **Step 1.1: Client Browses Professionals**
**Location:** `/professionals/` (Professional Directory)

**Actions:**
- Client views professional profiles with:
  - Name, specialization, rating, reviews
  - Hourly rate (reference only)
  - Portfolio, certifications
  - Availability status

**Outcome:** Client selects a professional

---

### **Step 1.2: Client Creates Request**
**Location:** `/requests/create/?professional=<id>`

**Required Fields:**
- Title (5-200 chars)
- Description (50-5000 chars)
- Category/Specialization
- **Budget (₱)** ← Client sets initial price
- Timeline (days)
- Attached files (optional)
- Pre-selected professional email

**Database Changes:**
```python
Request.objects.create(
    title="...",
    description="...",
    client=client.email,
    professional=professional.email,  # Pre-assigned
    status='pending',  # Awaiting professional response
    price=client_budget,  # Initial price
    timeline_days=7
)
```

**Outcome:** 
- Request created with status: `pending`
- Professional receives notification
- **NO transaction created yet** (only after acceptance)

---

## **PHASE 2: Professional Response & Price Negotiation**

### **Step 2.1: Professional Reviews Request**
**Location:** `/dashboard/` (Professional Dashboard)

**Professional sees:**
- Request details
- Client's proposed budget: `₱5,000`
- Timeline
- Attached files

**Actions:**
1. **Accept** (proceed to price setting) ✅
2. **Decline** (request marked as `declined`) ❌

---

### **Step 2.2: Professional Accepts & Sets Price**
**Location:** `/requests/<id>/accept/` (Modal/Form)

**Professional Actions:**
- Reviews client's budget: `₱5,000`
- Options:
  - **Accept client's price** → `₱5,000`
  - **Propose different price** → `₱7,500` (with explanation)

**Database Changes:**
```python
# Update request
request.price = professional_price  # ₱7,500
request.status = 'pending'  # Still pending (awaiting client payment)
request.price_negotiation_status = 'proposed'  # New field
request.professional_price_notes = "Requires additional research..."

# Create Transaction
Transaction.objects.create(
    request=request,
    client=client,
    professional=professional,
    amount=professional_price,  # ₱7,500
    status='pending_payment',  # Awaiting client payment
    payment_method='gcash'
)

# Create Conversation
Conversation.objects.create(
    request=request,
    client=client,
    professional=professional
)
```

**Outcome:**
- Request: `pending` (awaiting payment)
- Transaction: `pending_payment`
- Professional can message client about price
- Client receives notification: "Professional accepted but proposed ₱7,500"

---

### **Step 2.3: Client Reviews Price (NEGOTIATION)**
**Location:** Request detail page or notification

**Client Options:**

#### **Option A: Accept Professional's Price**
```python
transaction.amount = professional_price  # ₱7,500
request.price_negotiation_status = 'agreed'
# Redirect to payment page
```

#### **Option B: Counter-Offer**
```python
request.price = new_client_offer  # ₱6,500
request.price_negotiation_status = 'counter_offered'
transaction.amount = new_client_offer
# Notify professional
```

#### **Option C: Cancel Request**
```python
request.status = 'cancelled'
transaction.delete()  # No payment made yet
```

**Negotiation Flow:**
- Max 3 rounds of negotiation (configurable)
- After 3 rounds, both must agree or cancel
- All negotiation happens via messaging system

**Outcome:** 
- Once agreed: Transaction amount finalized
- Client proceeds to payment

---

## **PHASE 3: Payment (Escrow)**

### **Step 3.1: Client Makes Payment**
**Location:** `/transactions/<id>/pay/`

**Payment Details Shown:**
```
Service Fee:        ₱7,500.00
Platform Fee (10%): ₱750.00
Total to Pay:       ₱7,500.00

Professional Gets:  ₱6,750.00 (after 10% fee)
```

**Payment Method: GCash**

**Required Information:**
- GCash Number (client's)
- GCash Reference Number
- Screenshot of GCash receipt

**Pay To:**
- ProLink GCash: `09XX-XXX-XXXX`
- Name: `ProLink Services`

**Database Changes:**
```python
# Update Transaction
transaction.gcash_number = client_gcash_number
transaction.transaction_id = gcash_reference_number
transaction.gcash_screenshot = uploaded_screenshot_url
transaction.status = 'escrowed'  # Payment received
transaction.paid_at = timezone.now()
transaction.save()

# Update Request
request.status = 'in_progress'  # Work can begin
request.save()
```

**Outcome:**
- Money held in ProLink's escrow account
- Request: `in_progress`
- Transaction: `escrowed`
- Professional can start work
- Professional receives notification: "Payment received! You can start working"

---

## **PHASE 4: Work & Submission**

### **Step 4.1: Professional Works on Request**
**Location:** Professional workspace

**Professional Actions:**
- Access request details
- Communicate with client via messaging
- Prepare deliverables
- Upload work when ready

**Request Status:** `in_progress`
**Transaction Status:** `escrowed`

---

### **Step 4.2: Professional Submits Work**
**Location:** `/transactions/<id>/submit-work/`

**Required:**
- Deliverable files (at least 1)
- Deliverable notes/description

**Database Changes:**
```python
# Update Request
request.deliverable_files = json.dumps(uploaded_files)
request.deliverable_notes = professional_notes
request.status = 'under_review'  # Client must review
request.submitted_at = timezone.now()
request.revision_count = 0  # Initialize revision counter
request.save()

# Update Transaction
transaction.status = 'pending_approval'  # Awaiting client decision
transaction.save()
```

**Outcome:**
- Request: `under_review`
- Transaction: `pending_approval`
- Client receives notification: "Work submitted for review"

---

## **PHASE 5: Client Review & Decision**

### **Step 5.1: Client Reviews Work**
**Location:** `/requests/<id>/review/`

**Client Sees:**
- Original request details
- Professional's deliverables (download links)
- Professional's notes
- Revision count: `0 / 3`

**Client Has 3 Options:**

---

### **Option A: APPROVE WORK ✅**

**Action:** Client clicks "Approve & Release Payment"

**Database Changes:**
```python
# Update Request
request.status = 'completed'
request.completed_at = timezone.now()
request.save()

# Update Transaction
transaction.status = 'completed'
transaction.released_at = timezone.now()
transaction.save()

# Create notifications
# - Professional: "Payment released! ₱6,750.00 is on the way"
# - Client: "Thank you! You can now leave a review"
```

**Money Movement:**
- ProLink transfers `₱6,750` to professional's account
- ProLink keeps `₱750` as platform fee (10%)

**Outcome:**
- Request: `completed`
- Transaction: `completed`
- Both can leave reviews
- **WORKFLOW ENDS** ✅

---

### **Option B: REQUEST REVISION 🔄**

**Action:** Client clicks "Request Changes"

**Required:**
- Revision notes (what needs to be changed)
- Can attach additional reference files

**Revision Limit Check:**
```python
if request.revision_count >= 3:
    # Cannot request more revisions
    messages.error("Maximum revisions reached (3). Please approve or open a dispute.")
    return redirect(...)
```

**Database Changes:**
```python
# Update Request
request.status = 'revision_requested'
request.revision_notes = client_feedback
request.revision_count += 1  # 0 → 1
request.save()

# Transaction stays: 'pending_approval'
# (Money still in escrow)
```

**Outcome:**
- Request: `revision_requested`
- Transaction: `pending_approval` (unchanged)
- Professional receives notification with revision details
- **Returns to Step 4.2** (Professional resubmits)

**Revision Cycle:**
1. Client requests revision (revision_count = 1)
2. Professional resubmits → Request: `under_review`
3. Client requests revision again (revision_count = 2)
4. Professional resubmits → Request: `under_review`
5. Client requests revision again (revision_count = 3) ← **LAST REVISION**
6. Professional resubmits → Request: `under_review`
7. Client **MUST** either approve or dispute (no more revisions)

---

### **Option C: OPEN DISPUTE ⚠️**

**Action:** Client clicks "Open Dispute"

**When to Use:**
- Work quality unacceptable after 3 revisions
- Professional not responding
- Deliverables don't match description
- Fraudulent activity

**Required:**
- Reason for dispute
- Evidence (screenshots, messages, files)
- Description of issue

**Database Changes:**
```python
# Update Request
request.status = 'disputed'
request.save()

# Update Transaction
transaction.status = 'disputed'
transaction.save()

# Create Dispute
Dispute.objects.create(
    transaction=transaction,
    opened_by=client,
    reason=client_reason,
    client_evidence=client_evidence_text,
    client_files=json.dumps(client_evidence_files),
    status='open'
)
```

**Outcome:**
- Request: `disputed`
- Transaction: `disputed`
- Money frozen in escrow
- Admin receives notification
- **Proceeds to Dispute Resolution** (Phase 6)

---

## **PHASE 6: Dispute Resolution (Admin Only)**

### **Step 6.1: Admin Reviews Dispute**
**Location:** `/admin/transactions/dispute/<id>/`

**Admin Sees:**
- Complete request history
- Original request & deliverables
- All messages between parties
- Client's evidence
- Professional's response (if any)
- Transaction details

**Admin Can Request More Info:**
- Ask professional to respond
- Request additional evidence from either party

---

### **Step 6.2: Professional Responds to Dispute**
**Location:** Notification → Response form

**Professional Provides:**
- Counter-evidence
- Explanation of situation
- Supporting files

**Database Changes:**
```python
dispute.professional_evidence = pro_response
dispute.professional_files = json.dumps(pro_files)
dispute.status = 'under_review'
dispute.save()
```

---

### **Step 6.3: Admin Makes Decision**

**Admin Has 3 Options:**

#### **Option A: Full Refund to Client**
```python
dispute.status = 'resolved_client'
dispute.refund_amount = transaction.amount  # Full refund
dispute.resolution_notes = admin_decision
dispute.resolved_by = admin_user
dispute.resolved_at = timezone.now()
dispute.save()

# Update Transaction
transaction.status = 'refunded'
transaction.save()

# Update Request
request.status = 'cancelled'
request.save()

# Money returned to client
# Professional gets nothing (0% payout)
```

**Use When:**
- Professional clearly failed to deliver
- Fraudulent behavior
- Work completely unusable

---

#### **Option B: Full Payment to Professional**
```python
dispute.status = 'resolved_professional'
dispute.refund_amount = 0
dispute.resolution_notes = admin_decision
dispute.resolved_by = admin_user
dispute.resolved_at = timezone.now()
dispute.save()

# Update Transaction
transaction.status = 'completed'
transaction.released_at = timezone.now()
transaction.save()

# Update Request
request.status = 'completed'
request.save()

# Professional gets full payout (90% of amount)
# Client gets nothing back
```

**Use When:**
- Client unreasonably rejecting good work
- Professional met all requirements
- Dispute unwarranted

---

#### **Option C: Partial Refund (Not Implemented - Future)**
```python
# Example: 50% to each party
dispute.status = 'resolved_partial'
dispute.refund_amount = transaction.amount * 0.5
dispute.resolution_notes = admin_decision
dispute.save()

# Complex: Requires partial payment system
# For MVP: Only full refund or full payment
```

---

## **📈 State Diagram**

```
[Client Creates Request]
         ↓
    [pending] ← Professional not responded yet
         ↓
[Professional Accepts & Sets Price]
         ↓
    [pending] ← Transaction: pending_payment
         ↓
[Client Pays (GCash)]
         ↓
   [in_progress] ← Transaction: escrowed
         ↓
[Professional Submits Work]
         ↓
  [under_review] ← Transaction: pending_approval
         ↓
[Client Reviews]
    ↙     ↓     ↘
[APPROVE] [REVISE] [DISPUTE]
    ↓      ↓         ↓
[completed] ←→ [revision_requested] → [disputed]
             (max 3 times)              ↓
                                   [Admin Resolves]
                                    ↙         ↘
                              [refunded]  [completed]
```

---

## **🔒 Business Rules**

### **Payment Rules**
1. Client pays **before** work begins (escrow)
2. Money held until client approves OR admin resolves dispute
3. Professional gets 90%, ProLink gets 10%
4. No partial payments (for MVP)

### **Revision Rules**
1. Maximum **3 revisions** per request
2. Revisions are included in original price (no extra charge)
3. After 3 revisions, client must approve or dispute
4. Revision requests must include specific feedback

### **Dispute Rules**
1. Only client can open dispute
2. Disputes freeze transaction immediately
3. Admin decision is final
4. Outcomes: Full refund OR Full payment (no partial for MVP)
5. Both parties can provide evidence

### **Cancellation Rules**
1. **Before Payment:** Either party can cancel (no penalty)
2. **After Payment:** Requires dispute resolution
3. Professional declining = automatic cancellation

---

## **🚨 Edge Cases & Error Handling**

### **Case 1: Professional Accepts but Client Never Pays**
**Scenario:** Professional accepted, set price, but client disappeared

**Current State:**
- Request: `pending`
- Transaction: `pending_payment`

**Solution:**
- Auto-cancel after 7 days of no payment
- Professional can manually cancel after 48 hours
- No penalty to either party

**Implementation:**
```python
# Cron job or management command
from datetime import timedelta
from django.utils import timezone

old_pending = Transaction.objects.filter(
    status='pending_payment',
    created_at__lt=timezone.now() - timedelta(days=7)
)

for transaction in old_pending:
    transaction.request.status = 'cancelled'
    transaction.request.save()
    transaction.delete()  # No payment was made
```

---

### **Case 2: Professional Accepts but Never Submits Work**
**Scenario:** Client paid, but professional disappeared

**Current State:**
- Request: `in_progress`
- Transaction: `escrowed`

**Solution:**
- Client can open dispute after deadline + 3 days
- Client provides evidence: "Professional not responding"
- Admin refunds client (100%)
- Professional account flagged/banned

---

### **Case 3: Client Approves but Payment Release Fails**
**Scenario:** Client clicked approve, but GCash transfer to professional failed

**Current State:**
- Request: `completed`
- Transaction: `completed` but `released_at` is set, money not transferred

**Solution:**
- Admin manually processes payment
- Transaction log tracks all money movements
- Professional notified of delay
- Issue resolved within 24 hours

---

### **Case 4: Both Parties Ghost After Submission**
**Scenario:** Work submitted, client never reviews, professional doesn't follow up

**Current State:**
- Request: `under_review`
- Transaction: `pending_approval`
- Money in escrow

**Solution:**
- Auto-approve after 7 days of no client response
- Send client reminders at day 3 and day 6
- After auto-approve: Payment released to professional

**Implementation:**
```python
# Cron job
auto_approve_date = timezone.now() - timedelta(days=7)
pending_reviews = Request.objects.filter(
    status='under_review',
    submitted_at__lt=auto_approve_date
)

for req in pending_reviews:
    req.status = 'completed'
    req.completed_at = timezone.now()
    req.save()
    
    transaction = req.transaction
    transaction.status = 'completed'
    transaction.released_at = timezone.now()
    transaction.save()
    
    # Notify both parties
```

---

### **Case 5: Duplicate Payments**
**Scenario:** Client accidentally pays twice (submits form twice)

**Solution:**
- Check for existing payment before creating new transaction
- Unique constraint on `transaction_id` (GCash reference)
- Show error: "This GCash reference has already been used"

---

### **Case 6: Price Negotiation Never Ends**
**Scenario:** Client and professional keep counter-offering forever

**Solution:**
- Maximum 5 negotiation rounds
- After 5 rounds, either party can cancel
- Message: "Price negotiation limit reached. Please finalize or cancel."

---

## **📱 Notification Plan**

| Event | Notify Client | Notify Professional |
|-------|---------------|---------------------|
| Request created | ✅ Confirmation | ✅ New request |
| Professional accepts | ✅ Price proposal | ✅ Confirmation |
| Price agreed | ✅ Payment reminder | ✅ Awaiting payment |
| Payment received | ✅ Receipt | ✅ Start work |
| Work submitted | ✅ Review reminder | ✅ Confirmation |
| Revision requested | ✅ Request sent | ✅ Revision details |
| Work approved | ✅ Thank you | ✅ Payment released |
| Dispute opened | ✅ Confirmation | ✅ Response needed |
| Dispute resolved | ✅ Outcome | ✅ Outcome |

---

## **🧪 Testing Scenarios**

### **Happy Path**
1. Client creates request → Professional accepts → Client pays → Professional submits → Client approves → **COMPLETED** ✅

### **Revision Path**
1. Client creates → Professional accepts → Client pays → Professional submits → Client requests revision (1) → Professional resubmits → Client approves → **COMPLETED** ✅

### **Maximum Revisions**
1. Client creates → Professional accepts → Client pays → Professional submits → Revision 1 → Revision 2 → Revision 3 → Client MUST approve or dispute

### **Dispute - Client Wins**
1. Client creates → Professional accepts → Client pays → Professional submits → Client disputes → Admin reviews → Full refund → **REFUNDED**

### **Dispute - Professional Wins**
1. Client creates → Professional accepts → Client pays → Professional submits → Client disputes → Admin reviews → Full payment → **COMPLETED**

### **Negotiation Flow**
1. Client proposes ₱5,000 → Professional counters ₱7,500 → Client counters ₱6,500 → Professional accepts ₱6,500 → Client pays → Work continues

### **Cancellation Before Payment**
1. Client creates → Professional accepts → Client cancels → **CANCELLED** (no penalty)

### **Professional Declines**
1. Client creates → Professional declines → **DECLINED** (no penalty)

---

## **🔧 Required Code Changes Summary**

### **1. Model Updates**
**File:** `requests/models.py`
```python
# Add to Request model:
revision_count = models.IntegerField(default=0)
max_revisions = models.IntegerField(default=3)
price_negotiation_status = models.CharField(...)
professional_price_notes = models.TextField(blank=True)
auto_approve_date = models.DateTimeField(null=True, blank=True)
```

**File:** `transactions/models.py`
```python
# Add 'disputed' to STATUS_CHOICES
# Already has Dispute model ✅
```

### **2. New Views Needed**
- `approve_work()` - Client approves deliverables
- `request_revision()` - Client requests changes
- `open_dispute()` - Client opens dispute
- `negotiate_price()` - Both parties negotiate
- Admin dispute resolution views

### **3. Templates Needed**
- `transactions/approve_work.html`
- `transactions/request_revision.html`
- `transactions/open_dispute.html`
- `transactions/price_negotiation.html`
- Admin dispute dashboard

### **4. Background Jobs**
- Auto-cancel unpaid requests (7 days)
- Auto-approve unreviewed work (7 days)
- Send review reminders (day 3, 6)

---

## **✅ What's Already Working**

1. ✅ Request creation with pre-selected professional
2. ✅ Professional accept/decline
3. ✅ Transaction creation on acceptance
4. ✅ GCash payment submission
5. ✅ Work submission by professional
6. ✅ Conversation/messaging system
7. ✅ Transaction history
8. ✅ Dispute model structure

---

## **🚀 Implementation Priority**

### **Phase 1 (Critical - Do First)**
1. Fix status synchronization
2. Add approve/reject work views
3. Implement revision system
4. Add auto-approve after 7 days

### **Phase 2 (Important)**
1. Price negotiation system
2. Dispute opening flow
3. Admin dispute resolution

### **Phase 3 (Enhancement)**
1. Background jobs (auto-cancel, reminders)
2. Advanced analytics
3. Review system integration
4. Partial refunds (future)

---

## **📊 Metrics to Track**

- Average time to completion
- Revision rate (% of requests requiring revisions)
- Dispute rate (% of transactions disputed)
- Payment success rate
- Professional acceptance rate
- Auto-approval rate (ghosted clients)
- Platform fee revenue

---

**END OF USER FLOW DOCUMENTATION**
