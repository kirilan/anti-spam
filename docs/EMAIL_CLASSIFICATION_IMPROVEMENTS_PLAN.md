# Email Classification & User Action Improvements - Implementation Plan

## Status Summary

### ✅ Previously Implemented (from ENHANCED_EMAIL_SCANNING_PLAN.md)
The following features have been **successfully implemented** and are in production:

1. ✅ **Sent email scanning** - Scans user's sent folder for broker emails
2. ✅ **Auto-create deletion requests** - Creates requests from discovered sent emails
3. ✅ **Thread tracking** - Gmail thread IDs captured and displayed
4. ✅ **Email direction tracking** - Distinguishes sent vs received emails
5. ✅ **Response classification** - ResponseDetector classifies broker replies
6. ✅ **Thread view UI** - Full email conversation displayed in requests
7. ✅ **Auto-discovery source** - Tracks if request was manual or auto-discovered
8. ✅ **Response-based status updates** - Auto-sets status based on response type

**Bug Fixed (2025-12-24):**
- ✅ Email direction now correctly identifies sent emails even when they appear in inbox (thread participants)

---

## 🎯 New Improvements Required

### Priority 1: Enhanced "Action Required" Response Type

#### Problem
Currently, REQUEST_INFO responses show as "Info Requested" in yellow, but users don't clearly understand they need to take action. Broker responses requesting additional information, identity verification, or asking users to fill web forms need more prominent indicators.

#### Solution: Dedicated "ACTION_REQUIRED" Response Type

**1. Backend Changes**

**File:** `backend/app/models/broker_response.py`
```python
class ResponseType(str, enum.Enum):
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    ACKNOWLEDGMENT = "acknowledgment"
    ACTION_REQUIRED = "action_required"  # NEW - Replaces REQUEST_INFO for user actions
    REQUEST_INFO = "request_info"         # Keep for legacy/informational responses
    UNKNOWN = "unknown"
```

**File:** `backend/app/services/response_detector.py`

Update keyword lists:

```python
# NEW - Strong action required indicators
ACTION_REQUIRED_KEYWORDS = [
    # Identity verification (requires user action)
    "verify your identity",
    "confirm your identity",
    "verify that you are",
    "prove your identity",
    "identity verification required",
    "verification required",
    "complete verification",

    # Webform/online action required
    "fill out form",
    "complete the form",
    "submit the form",
    "complete your request online",
    "visit our website to",
    "go to our website",
    "click the link below to",
    "use our online form",
    "online request form",

    # Additional information required with urgency
    "must provide",
    "you must submit",
    "required to complete",
    "need you to",
    "please provide the following",
    "action required",
    "action needed",
    "respond to this email",
    "reply with",
    "send us",

    # Document requests
    "provide documentation",
    "upload documents",
    "attach a copy",
    "send proof of",
    "proof of residency",
    "government-issued ID",
    "driver's license",
    "utility bill",
]

# Keep REQUEST_INFO for softer informational responses
REQUEST_INFO_KEYWORDS = [
    "need more information",
    "need additional information",
    "additional details",
    "may need",
    "might require",
    "could you provide",

    # Instructions without urgency
    "removal instructions",
    "opt-out instructions",
    "deletion instructions",
    "how to remove",
    "how to delete",
    "follow these steps",
    "to opt out",
]
```

**Classification priority** (in `detect_response_type()`):
1. Check ACTION_REQUIRED first (highest priority for user actions)
2. Then CONFIRMATION
3. Then REJECTION
4. Then ACKNOWLEDGMENT
5. Then REQUEST_INFO
6. Finally UNKNOWN

**2. Frontend Changes**

**File:** `frontend/src/components/requests/RequestList.tsx`

Update response type configuration:

```typescript
const responseTypeConfig: Record<BrokerResponseType, {
  label: string;
  color: string;
  bg: string;
  icon: any;
  tooltip?: string;  // NEW - Add tooltip support
}> = {
  confirmation: {
    label: 'Confirmation',
    color: 'text-green-600',
    bg: 'bg-green-50',
    icon: CheckCircle
  },
  rejection: {
    label: 'Rejection',
    color: 'text-red-600',
    bg: 'bg-red-50',
    icon: XCircle
  },
  acknowledgment: {
    label: 'Acknowledged',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    icon: Clock
  },
  action_required: {  // NEW
    label: 'Action Required',
    color: 'text-orange-600',  // More urgent than yellow
    bg: 'bg-orange-50',
    icon: AlertTriangle,  // Warning triangle icon
    tooltip: 'This broker requires you to take action. They may be asking for identity verification, additional documents, or to fill out a web form. Review the response below for details.'
  },
  request_info: {
    label: 'Info Requested',
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    icon: AlertCircle
  },
  unknown: {
    label: 'Unknown',
    color: 'text-gray-600',
    bg: 'bg-gray-50',
    icon: HelpCircle
  },
}
```

**Add prominent visual indicator** for ACTION_REQUIRED responses:

```typescript
// In RequestCard component
{latestResponse && latestResponse.response_type === 'action_required' && (
  <div className="mt-2 rounded-lg border-2 border-orange-400 bg-orange-50 p-3">
    <div className="flex items-start gap-2">
      <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
      <div>
        <p className="text-sm font-semibold text-orange-900">
          Action Required
        </p>
        <p className="text-xs text-orange-800 mt-1">
          The broker has responded and needs you to take action before they can
          process your deletion request. Check the response below for details.
        </p>
      </div>
    </div>
  </div>
)}
```

**Add tooltip to response badges:**

```typescript
// When displaying response badge
<div className="relative group">
  <Badge variant="outline" className={`${responseConfig.bg} ${responseConfig.color}`}>
    <Icon className="h-3 w-3 mr-1" />
    {responseConfig.label}
  </Badge>
  {responseConfig.tooltip && (
    <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
      <div className="bg-gray-900 text-white text-xs rounded py-2 px-3 max-w-xs">
        {responseConfig.tooltip}
        <div className="absolute top-full left-4 -mt-1">
          <div className="border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
  )}
</div>
```

**3. UI Enhancements for All Response Types**

**Response message preview expansion:**
- Currently emails in thread view have collapsed/expanded state
- ✅ Already implemented (lines 874-900 in RequestList.tsx)

**Response action guidance:**
Add helpful text based on response type:

```typescript
const getActionGuidance = (responseType: string): string | null => {
  switch (responseType) {
    case 'action_required':
      return 'Review the broker\'s response below and follow their instructions. This may require you to verify your identity, provide documents, or fill out a web form.'
    case 'confirmation':
      return 'Your data has been deleted. No further action needed.'
    case 'rejection':
      return 'The broker rejected your request. Review their reason below. You may need to contact them directly or use their web portal.'
    case 'acknowledgment':
      return 'The broker has received your request and is processing it. Check back later for updates.'
    case 'request_info':
      return 'The broker has provided information about their deletion process. Review their instructions below.'
    default:
      return null
  }
}
```

**4. Request Status Updates**

Update `_analyze_received_email_status()` in `email_scanner.py`:

```python
# If high confidence that this is a response to a deletion request
if confidence >= 0.6:
    if response_type == ResponseType.CONFIRMATION:
        return RequestStatus.CONFIRMED
    elif response_type == ResponseType.REJECTION:
        return RequestStatus.REJECTED
    elif response_type == ResponseType.ACTION_REQUIRED:  # NEW
        return RequestStatus.SENT  # Keep as SENT but highlight response
    # For acknowledgment, info_request, or unknown - treat as sent
    else:
        return RequestStatus.SENT
```

**File:** `backend/app/models/deletion_request.py`

Consider adding new status (OPTIONAL - for future):
```python
class RequestStatus(str, enum.Enum):
    PENDING = "pending"              # Draft, not sent
    SENT = "sent"                    # Email sent, awaiting response
    ACTION_REQUIRED = "action_required"  # NEW - Broker needs user action
    CONFIRMED = "confirmed"          # Deletion confirmed
    REJECTED = "rejected"            # Deletion rejected
```

---

### Priority 2: Improved Request Status Indicators

**Problem:**
Requests with ACTION_REQUIRED responses should be visually distinct from regular SENT requests.

**Solution:**

Update status badge configuration in `RequestList.tsx`:

```typescript
const statusConfig = {
  pending: {
    icon: Clock,
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    label: 'Pending'
  },
  sent: {
    icon: Mail,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    label: 'Sent'
  },
  action_required: {  // NEW
    icon: AlertTriangle,
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    label: 'Action Required'
  },
  response_received: {
    icon: MessageSquare,
    color: 'text-cyan-600',
    bg: 'bg-cyan-500/10',
    label: 'Response received'
  },
  confirmed: {
    icon: CheckCircle,
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    label: 'Confirmed'
  },
  rejected: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    label: 'Rejected'
  },
}

// Determine status key with ACTION_REQUIRED check
const hasActionRequired = responses.some(r => r.response_type === 'action_required')
const statusKey = hasActionRequired && request.status === 'sent'
  ? 'action_required'
  : (hasResponse && request.status === 'sent' ? 'response_received' : request.status)
```

---

### Priority 3: Response Summary Dashboard Widget

**NEW FEATURE**

Add a dashboard widget showing:
- Requests needing action (ACTION_REQUIRED responses)
- Pending requests (not yet sent)
- Confirmed deletions
- Rejected requests

**File:** `frontend/src/components/dashboard/ResponseSummary.tsx`

```typescript
interface ResponseSummary {
  action_required_count: number
  pending_count: number
  sent_awaiting_response: number
  confirmed_count: number
  rejected_count: number
}

// API endpoint: GET /analytics/response-summary
```

Display in dashboard:
- Orange card for Action Required (most prominent)
- Yellow card for Pending
- Blue card for Sent (awaiting response)
- Green card for Confirmed
- Red card for Rejected

Click on card → filters request list to show only that type

---

### Priority 4: Email Notifications (Future Enhancement)

**Not Yet Implemented - For Future Consideration**

Send email notifications to users when:
1. Broker responds with ACTION_REQUIRED
2. Broker confirms deletion
3. Broker rejects deletion request

Requires:
- User email preferences table
- Email service integration (SendGrid/SES)
- Email templates
- Notification queue system

---

## Implementation Order

### Phase 1: Backend Classification (1-2 hours)
1. Add ACTION_REQUIRED to ResponseType enum
2. Update ResponseDetector keywords
3. Adjust classification priority logic
4. Update status determination logic
5. Run backend tests

### Phase 2: Frontend UI (2-3 hours)
1. Update response type configuration with ACTION_REQUIRED
2. Add prominent visual indicator for action required responses
3. Add tooltips to response badges
4. Update status badge logic
5. Add action guidance messages
6. Test UI changes

### Phase 3: Testing & Migration (1-2 hours)
1. Test with real broker emails
2. Backfill existing REQUEST_INFO responses (SQL update)
3. Verify UI displays correctly
4. Update documentation

### Phase 4: Dashboard Widget (2-3 hours) - OPTIONAL
1. Create ResponseSummary component
2. Add API endpoint for summary stats
3. Add to main dashboard
4. Wire up filtering

**Total Estimated Time: 6-10 hours**

---

## Database Migration Notes

**Reclassify existing REQUEST_INFO responses:**

```sql
-- After deploying code changes, reclassify existing responses
-- Run this query to identify which REQUEST_INFO responses should be ACTION_REQUIRED

SELECT
    br.id,
    br.subject,
    br.body_text,
    br.response_type,
    br.confidence_score
FROM broker_responses br
WHERE br.response_type = 'request_info'
AND br.confidence_score >= 0.6
AND (
    br.body_text ILIKE '%verify your identity%'
    OR br.body_text ILIKE '%fill out form%'
    OR br.body_text ILIKE '%action required%'
    OR br.body_text ILIKE '%provide documentation%'
    OR br.body_text ILIKE '%visit our website%'
    OR br.body_text ILIKE '%click the link%'
);

-- Then re-run response detection on these to get new classification
-- Or manually update high-confidence ones:
-- UPDATE broker_responses
-- SET response_type = 'action_required'
-- WHERE id IN (...);
```

---

## Testing Checklist

- [ ] ACTION_REQUIRED classification works for identity verification emails
- [ ] ACTION_REQUIRED classification works for webform request emails
- [ ] ACTION_REQUIRED classification works for document request emails
- [ ] REQUEST_INFO still works for softer informational responses
- [ ] Orange badge and warning appear for ACTION_REQUIRED responses
- [ ] Tooltip displays correctly on hover
- [ ] Action guidance text shows appropriate message
- [ ] Status badge updates to "Action Required" when appropriate
- [ ] Manual reclassification dropdown includes new type
- [ ] Response summary in responses section displays correctly
- [ ] Thread view shows ACTION_REQUIRED responses properly
- [ ] Email direction bug is fixed (sent emails show as "Sent" not "Received")

---

## Success Metrics

**User Understanding:**
- Users can clearly identify when broker needs them to take action
- Users understand what action is required
- Users know where to find broker's instructions

**Classification Accuracy:**
- 90%+ of identity verification requests classified as ACTION_REQUIRED
- 90%+ of webform requests classified as ACTION_REQUIRED
- 90%+ of document requests classified as ACTION_REQUIRED
- < 10% false positives (informational emails marked as ACTION_REQUIRED)

**User Engagement:**
- Users respond to ACTION_REQUIRED requests faster than before
- Reduction in confused user support requests
- Increase in successful deletions (users complete verification)

---

## Related Files

### Backend:
- `backend/app/models/broker_response.py` - ResponseType enum
- `backend/app/services/response_detector.py` - Classification logic
- `backend/app/services/email_scanner.py` - Status determination (FIXED email_direction bug)
- `backend/app/api/responses.py` - Response endpoints
- `backend/app/schemas/response.py` - Pydantic schemas

### Frontend:
- `frontend/src/components/requests/RequestList.tsx` - Request cards and response display
- `frontend/src/components/dashboard/Dashboard.tsx` - Main dashboard (for future widget)
- `frontend/src/types/index.ts` - TypeScript types
- `frontend/src/hooks/useResponses.ts` - Response data hooks

---

## Notes

**Why separate ACTION_REQUIRED from REQUEST_INFO?**
- REQUEST_INFO is too generic and doesn't convey urgency
- Users need clear visual indicator that broker is waiting for them
- Different UI treatment needed for actionable vs informational responses
- Allows filtering/sorting requests by action needed

**Why orange instead of red?**
- Red typically means error/failure (rejection)
- Orange conveys urgency without panic
- Distinct from yellow (pending) and red (rejected)
- Standard UI convention for "attention needed" states

**Why not add new request status?**
- Keeps status model simple (pending/sent/confirmed/rejected)
- Status represents request lifecycle, not response type
- Response type already captures the nuance
- Can derive "action required" state from responses without status change

---

**Last Updated:** 2025-12-24
**Status:** Ready for Implementation
**Previous Plan:** `ENHANCED_EMAIL_SCANNING_PLAN.md` (archived - features implemented)
