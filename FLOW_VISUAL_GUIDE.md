# 🎯 ProLink Complete Flow - Quick Reference

## 🔄 The Complete Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT CREATES REQUEST                      │
│  📝 Title, Description, Budget (₱5,000), Timeline, Professional │
│                     Status: PENDING                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PROFESSIONAL REVIEWS & RESPONDS                     │
│  👀 Views request details and client's proposed budget          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Accept ₱5,000│  │ Propose ₱7,500│  │   Decline    │         │
│  │   AS-IS      │  │  + Explain    │  │   Request    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↓                  ↓                  ↓                  │
│    Skip to PAYMENT    GO TO NEGOTIATION   END (Declined)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               PRICE NEGOTIATION (Max 5 Rounds)                  │
│  💬 Client sees: ~~₱5,000~~ → ₱7,500                            │
│  📝 Professional's explanation displayed                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Accept ₱7,500│  │Counter ₱6,500│  │    Cancel    │         │
│  │  & Pay Now   │  │  + Explain   │  │   Request    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↓                  ↓                  ↓                  │
│    GO TO PAYMENT    Back to Professional   END (Cancelled)     │
│                       (Round 2/5)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT PAYS VIA GCASH                        │
│  💳 Uploads GCash screenshot + reference number                 │
│  💰 Money goes into ESCROW                                      │
│                                                                  │
│  Request: PENDING → IN_PROGRESS                                │
│  Transaction: PENDING_PAYMENT → ESCROWED                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PROFESSIONAL WORKS ON REQUEST                      │
│  👨‍💻 Professional completes the work                             │
│  📤 Uploads deliverable files                                   │
│                                                                  │
│  Request: IN_PROGRESS → UNDER_REVIEW                           │
│  Transaction: ESCROWED → PENDING_APPROVAL                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CLIENT REVIEWS WORK                           │
│  👀 Views deliverable files                                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Approve    │  │   Request    │  │     Open     │         │
│  │ Release $$   │  │  Revision    │  │   Dispute    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↓                  ↓                  ↓                  │
│    COMPLETED        REVISION (3 max)     DISPUTED              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         COMPLETED                               │
│  ✅ Payment released to professional (90%)                      │
│  💰 Platform fee collected (10%)                                │
│  ⭐ Both parties can leave reviews                              │
│                                                                  │
│  Request: COMPLETED                                             │
│  Transaction: COMPLETED                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Status Reference

### Request Statuses
| Status | What It Means | Who Can Act |
|--------|---------------|-------------|
| 🟡 `pending` | Waiting for professional acceptance OR client payment | Professional OR Client |
| 🔵 `in_progress` | Professional is working | Professional |
| 🟣 `under_review` | Work submitted, client reviewing | Client |
| 🟠 `revision_requested` | Client wants changes | Professional |
| 🟢 `completed` | Done! Payment released | Both (reviews) |
| 🔴 `disputed` | Problem - admin reviewing | Admin |
| ⚫ `cancelled` | Ended early | None |
| ⚫ `declined` | Professional declined | None |

### Transaction Statuses
| Status | Money Location |
|--------|----------------|
| 🟡 `pending_payment` | Client hasn't paid yet |
| 🔵 `escrowed` | Held safely by ProLink |
| 🟣 `pending_approval` | Held, waiting for approval |
| 🟢 `completed` | Released to professional |
| 🔴 `disputed` | Frozen during dispute |
| ⚫ `refunded` | Returned to client |

### Price Negotiation Statuses
| Status | What It Means |
|--------|---------------|
| ⚪ `none` | No negotiation yet |
| 🟡 `proposed` | Professional proposed different price |
| 🟠 `counter_offered` | Client made counter-offer |
| 🟢 `agreed` | Price finalized, ready for payment |
| ⚫ `cancelled` | Negotiation cancelled |

---

## 🎨 What Each Page Looks Like

### 1️⃣ Professional Acceptance Page
```
┌───────────────────────────────────────────────────┐
│ 📝 Request Title                    💰 ₱5,000.00  │
│ 👤 Client: client@email.com                       │
├───────────────────────────────────────────────────┤
│                                                    │
│ Description:                                       │
│ "I need help with my thesis about..."            │
│                                                    │
│ Timeline: 7 days • Created: Nov 15, 2025          │
│                                                    │
├───────────────────────────────────────────────────┤
│ Choose Your Response:                              │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ ☑ Accept Client's Budget                    │  │
│ │   Accept ₱5,000 and start immediately       │  │
│ └─────────────────────────────────────────────┘  │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ ○ Propose Different Price                   │  │
│ │   Your Price: ₱ [______]                    │  │
│ │   Explanation: [____________]  (20+ chars)  │  │
│ └─────────────────────────────────────────────┘  │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ ○ Decline Request                           │  │
│ └─────────────────────────────────────────────┘  │
│                                                    │
│ [Submit Response]  [Cancel]                       │
└───────────────────────────────────────────────────┘
```

### 2️⃣ Price Negotiation Page
```
┌───────────────────────────────────────────────────┐
│          📝 Request Title                          │
│     Review Professional's Price Proposal           │
├───────────────────────────────────────────────────┤
│                                                    │
│  Your Budget      →    Professional's Price       │
│   ~~₱5,000~~           ₱7,500                     │
│                                                    │
│ ⚠️ Negotiation Round 1 of 5                       │
│    You have 4 more rounds to reach agreement      │
│                                                    │
│ 💬 Professional's Explanation:                    │
│ "This project requires advanced research and      │
│  multiple iterations. The complexity justifies    │
│  the higher rate."                                │
│                                                    │
├───────────────────────────────────────────────────┤
│ Choose Your Response:                              │
│                                                    │
│ ┌────────┐  ┌────────┐  ┌────────┐              │
│ │   ✅    │  │   ✏️    │  │   ❌    │              │
│ │ Accept  │  │Counter │  │ Cancel │              │
│ │  Price  │  │ Offer  │  │        │              │
│ └────────┘  └────────┘  └────────┘              │
│                                                    │
│ [Counter-Offer Form - appears when selected]      │
│ Your Price: ₱ [______]                            │
│ Explanation: [____________]  (20+ chars)          │
│                                                    │
│ [Submit Response]  [Back to Request]              │
└───────────────────────────────────────────────────┘
```

### 3️⃣ Client Dashboard Alert
```
┌───────────────────────────────────────────────────┐
│ 🤝 Price Negotiation - Response Needed            │
│                                                    │
│ My Thesis Project                                 │
│ 🏷️ Your budget: ₱5,000 → Professional proposed:   │
│    ₱7,500 • Round 1/5                             │
│                                         [Respond] │
└───────────────────────────────────────────────────┘
```

### 4️⃣ Professional Dashboard
```
┌───────────────────────────────────────────────────┐
│ Pending Requests                                   │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ My Thesis Project                           │  │
│ │ Client: client@email.com                    │  │
│ │ 🏷️ Client's Budget: ₱5,000                  │  │
│ │ Timeline: 7 days                            │  │
│ │                                             │  │
│ │ [View Details] [Accept Request]             │  │
│ └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

---

## ⚡ Quick Actions

### As Professional:
1. **Accept as-is:** Dashboard → Accept Request → Accept Client's Budget → Done
2. **Propose price:** Dashboard → Accept Request → Propose → Enter price + reason → Submit
3. **Decline:** Dashboard → Accept Request → Decline → Confirm

### As Client:
1. **Accept proposal:** Dashboard → Respond → Accept → Proceed to payment
2. **Counter-offer:** Dashboard → Respond → Counter-Offer → Enter price + reason → Submit
3. **Cancel:** Dashboard → Respond → Cancel → Confirm

---

## 🔍 How to Find Things

### Professional Looking For:
- **Pending requests:** Dashboard → "Pending Requests" section
- **Active projects:** Dashboard → "Active Projects" section
- **Negotiation updates:** Check email/notifications

### Client Looking For:
- **Price negotiations:** Dashboard → Yellow "Price Negotiation" alert (top)
- **Payment needed:** Dashboard → Red "Payment Required" alert
- **Work to review:** Dashboard → Green "Work Submitted" alert

---

## 💡 Pro Tips

### For Professionals:
- ✅ **Explain your pricing clearly** - clients appreciate transparency
- ✅ **Be fair** - reasonable prices lead to repeat clients
- ✅ **Respond quickly** - faster acceptance = faster earnings
- ⚠️ **Don't low-ball** - value your expertise appropriately

### For Clients:
- ✅ **Set realistic budgets** - quality work costs appropriate rates
- ✅ **Explain counter-offers** - help professionals understand your constraints
- ✅ **Negotiate respectfully** - good relationships = better results
- ⚠️ **Don't over-negotiate** - 5 rounds is the limit, be decisive

---

## 📞 Need Help?

### Common Questions:

**Q: What happens after 5 negotiation rounds?**  
A: You can only accept or cancel - no more counter-offers allowed.

**Q: Can I cancel after paying?**  
A: No, once paid you can only request revisions or open a dispute.

**Q: Who pays the platform fee?**  
A: Built into the price. If client pays ₱1,000, professional gets ₱900.

**Q: How long does professional have to accept?**  
A: No limit, but longer waits frustrate clients.

**Q: Can professional change price after acceptance?**  
A: No, price is locked after agreement.

---

## 🎉 You're Ready!

Server running at: `http://127.0.0.1:8000/`

Start testing the complete flow! 🚀
