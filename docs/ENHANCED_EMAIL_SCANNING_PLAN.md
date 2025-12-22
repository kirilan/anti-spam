# Enhanced Email Scanning System - Implementation Plan

## Summary

Enhance the email scanning system to:
1. Scan for SENT emails to broker domains (in addition to received)
2. Auto-create DeletionRequest records from discovered sent broker emails
3. Classify request status based on response content using ResponseDetector
4. Display full email thread history on deletion requests
5. Remove "show all emails" toggle - always show broker emails only

---

## 1. Database Schema Changes

### Migration: `add_email_scan_thread_support.py`

**EmailScan table additions:**
```python
gmail_thread_id = Column(String, nullable=True, index=True)  # Thread grouping
email_direction = Column(String, nullable=False, default='received')  # 'sent' or 'received'
```

**DeletionRequest table additions:**
```python
source = Column(String, default='manual')  # 'manual' or 'auto_discovered'
```

---

## 2. Backend Changes

### 2.1 Gmail Service (`backend/app/services/gmail_service.py`)

Add new methods:
- `list_sent_messages(user, query, max_results)` - Query sent folder
- `get_thread_messages(user, thread_id)` - Get all messages in a thread

### 2.2 Email Scanner (`backend/app/services/email_scanner.py`)

Enhance `scan_inbox()` to:
1. Scan received emails (existing) - capture `gmail_thread_id`
2. **NEW**: Scan sent emails to broker domains/privacy emails
3. Auto-create deletion requests for discovered sent emails
4. Analyze thread responses to set request status:
   - CONFIRMATION response → status = CONFIRMED
   - REJECTION response → status = REJECTED
   - ACKNOWLEDGMENT/REQUEST_INFO/No responses → status = SENT

New methods:
- `_scan_sent_broker_emails(user, days_back, max_emails)`
- `_auto_create_deletion_requests(user, sent_scans)`

### 2.3 Deletion Request Service (`backend/app/services/deletion_request_service.py`)

Add new methods:
- `create_request_from_discovery(user, broker, gmail_thread_id, gmail_message_id)` - Auto-create with duplicate check
- `get_thread_emails(request_id, user)` - Get all emails in thread for display

### 2.4 API Endpoints

**Modify** `/emails/scans/paged`:
- Remove `broker_only` parameter (always filter to broker emails)
- Add `direction` filter (`all`, `sent`, `received`)

**Add** `/requests/{request_id}/thread`:
- Return all emails in the thread for a deletion request
- Chronologically sorted with direction and response classification

---

## 3. Frontend Changes

### 3.1 EmailScanner Component (`frontend/src/components/emails/EmailScanner.tsx`)

Remove:
- `showBrokersOnly` state and toggle button
- Always show broker emails only

### 3.2 Hooks (`frontend/src/hooks/useEmails.ts`, `useRequests.ts`)

- Remove `brokerOnly` parameter from `useEmailScansPaged`
- Add `useRequestThread(requestId)` hook for thread emails

### 3.3 Request List (`frontend/src/components/requests/RequestList.tsx`)

Add thread view to show full email history:
- Sent email(s) from user
- Received responses from broker
- Chronological order with direction indicators

### 3.4 Types (`frontend/src/types/index.ts`)

Add:
```typescript
interface ThreadEmail {
  id: string
  gmail_message_id: string
  gmail_thread_id: string | null
  sender_email: string
  recipient_email: string | null
  subject: string | null
  body_preview: string | null
  direction: 'sent' | 'received'
  received_date: string | null
  response_type?: string | null
  confidence_score?: number | null
}
```

---

## 4. Critical Files to Modify

### Backend:
1. `backend/app/models/email_scan.py` - Add thread_id, direction columns
2. `backend/app/models/deletion_request.py` - Add source column
3. `backend/app/services/gmail_service.py` - Sent folder + thread methods
4. `backend/app/services/email_scanner.py` - Enhanced scanning logic
5. `backend/app/services/deletion_request_service.py` - Auto-create + thread retrieval
6. `backend/app/api/emails.py` - Update scans endpoint
7. `backend/app/api/requests.py` - Add thread endpoint
8. `backend/app/schemas/email.py` - Update EmailScan schema
9. `backend/app/schemas/request.py` - Add ThreadEmail schema
10. `backend/alembic/versions/` - New migration

### Frontend:
1. `frontend/src/components/emails/EmailScanner.tsx` - Remove toggle
2. `frontend/src/hooks/useEmails.ts` - Simplify hooks
3. `frontend/src/hooks/useRequests.ts` - Add thread hook
4. `frontend/src/components/requests/RequestList.tsx` - Thread view
5. `frontend/src/services/api.ts` - API methods
6. `frontend/src/types/index.ts` - New types

---

## 5. Implementation Order

### Phase 1: Database
1. Create Alembic migration for new columns
2. Update SQLAlchemy models
3. Apply migration

### Phase 2: Backend Services
1. Add Gmail service methods (sent folder, threads)
2. Enhance EmailScanner with sent email detection
3. Add auto-create deletion request logic with response analysis
4. Add thread retrieval to DeletionRequestService

### Phase 3: API Layer
1. Update `/emails/scans/paged` endpoint
2. Add `/requests/{request_id}/thread` endpoint
3. Update Pydantic schemas

### Phase 4: Frontend
1. Remove broker toggle from EmailScanner
2. Update hooks and API services
3. Add thread view component to RequestList
4. Update TypeScript types

### Phase 5: Testing
1. Backend unit tests for new scanner logic
2. Update frontend tests
3. Integration testing

---

## 6. Key Implementation Details

### Gmail Query for Sent Emails
```python
# Build query for sent emails to broker domains/privacy emails
broker_domains = [b.domains for b in brokers]  # All broker domains
privacy_emails = [b.privacy_email for b in brokers if b.privacy_email]

# Query: in:sent (to:@domain1.com OR to:@domain2.com OR to:privacy@...)
query = f"in:sent ({' OR '.join(f'to:{d}' for d in all_targets)}) after:{date}"
```

### Auto-Create Request Logic
```python
def _auto_create_deletion_requests(self, user, sent_scans):
    for scan in sent_scans:
        if not scan.broker_id:
            continue

        # Check for existing request
        existing = self.db.query(DeletionRequest).filter(
            DeletionRequest.user_id == user.id,
            DeletionRequest.broker_id == scan.broker_id
        ).first()

        if existing:
            # Update thread_id if not set
            continue

        # Analyze thread for responses
        thread_emails = self._get_thread_emails(scan.gmail_thread_id)
        status = self._analyze_thread_status(thread_emails)

        # Create request
        request = DeletionRequest(
            user_id=user.id,
            broker_id=scan.broker_id,
            status=status,
            source='auto_discovered',
            gmail_sent_message_id=scan.gmail_message_id,
            gmail_thread_id=scan.gmail_thread_id,
            sent_at=scan.received_date,  # Use email date
        )
```

### Response Analysis
```python
def _analyze_thread_status(self, thread_emails):
    """Analyze received emails in thread to determine status"""
    received = [e for e in thread_emails if e.email_direction == 'received']

    if not received:
        return RequestStatus.SENT  # No responses yet

    # Use ResponseDetector on each received email
    for email in received:
        response_type, confidence = self.response_detector.detect_response_type(
            email.subject, email.body_preview
        )

        if confidence >= 0.6:
            if response_type == ResponseType.CONFIRMATION:
                return RequestStatus.CONFIRMED
            elif response_type == ResponseType.REJECTION:
                return RequestStatus.REJECTED

    return RequestStatus.SENT  # Default if no clear classification
```

---

## Status: PLANNED (Not Yet Implemented)

This plan was created on 2025-12-22 and is ready for implementation when needed.
