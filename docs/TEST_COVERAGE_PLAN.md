# Test Coverage Extension Plan: Achieving 80% Coverage

## Progress Update (2025-12-25)

### Implemented So Far
- **Backend**: 44% → 55% coverage (30 → 140 tests)
- **Frontend**: 72% coverage (60 tests) - not started yet

### Tests Created
1. `test_analytics_service.py` - 15 tests (service: 16% → 99%)
2. `test_rate_limiter.py` - 15 tests (service: 0% → 100%)
3. `test_deletion_request_service.py` - 17 tests (service: 18% → 86%)
4. `test_activity_log_service.py` - 13 tests (service: 33% → 100%)
5. `test_response_matcher.py` - 13 tests (service: 22% → 93%)
6. `test_broker_detector.py` - 16 tests (service: 18% → 100%)
7. `test_gemini_service.py` - 16 tests (service: 22% → 80%)

### Still Needed for 80%
- Gmail service tests (17% coverage)
- Email scanner tests (8% coverage)
- Email tasks tests (11% coverage)
- API endpoint tests (17-42% coverage)
- Frontend hook tests

---

## Original State
- **Backend**: 44% coverage (30 tests)
- **Frontend**: 72% coverage (60 tests)
- **Target**: 80% for both

---

## Implementation Order (Confirmed: Backend First)

### Step 1: Setup & Foundation
1. Add `fakeredis` to dev dependencies in `pyproject.toml`
2. Add fixtures to `conftest.py` (deletion_request, broker_response, activity_log)

### Step 2: Backend Service Tests (No External Mocking)
3. `tests/test_analytics_service.py` - analytics_service.py (16%→90%)
4. `tests/test_rate_limiter.py` - rate_limiter.py (0%→90%) [uses fakeredis]
5. `tests/test_deletion_request_service.py` - deletion_request_service.py (18%→85%)
6. `tests/test_activity_log_service.py` - activity_log_service.py (33%→90%)
7. `tests/test_response_matcher.py` - response_matcher.py (22%→80%)

### Step 3: Backend External API Mocking
8. `tests/test_gmail_service.py` - gmail_service.py (17%→75%)
9. `tests/test_gemini_service.py` - gemini_service.py (22%→80%)
10. `tests/test_email_scanner.py` - email_scanner.py (8%→70%)

### Step 4: Backend API Endpoint Tests
11. `tests/test_analytics.py` - api/analytics.py (60%→90%)
12. `tests/test_auth.py` - api/auth.py (39%→85%)
13. `tests/test_requests.py` - api/requests.py (17%→75%)
14. `tests/test_emails.py` - api/emails.py (20%→75%)
15. `tests/test_admin.py` - api/admin.py (42%→85%)
16. `tests/test_ai.py` - api/ai.py (23%→80%)

### Step 5: Backend Celery Tasks
17. `tests/test_email_tasks.py` - tasks/email_tasks.py (11%→60%)

### Step 6: Frontend Tests
18. `src/services/__tests__/api.test.ts` - api.ts (37%→85%)
19. `src/hooks/__tests__/useEmails.test.ts`
20. `src/hooks/__tests__/useResponses.test.ts`
21. `src/hooks/__tests__/useActivities.test.ts`
22. `src/hooks/__tests__/useAdmin.test.ts`
23. `src/hooks/__tests__/useAI.test.ts`

---

## Dependencies to Add

### Backend (`pyproject.toml`):
```toml
fakeredis = ">=2.20.0"
pytest-mock = ">=3.12.0"
```

### Frontend (none required - MSW already set up)

---

## Expected Coverage After Implementation

| Component | Current | Target | New Tests |
|-----------|---------|--------|-----------|
| **Backend** | 44% | 80%+ | ~150 tests |
| **Frontend** | 72% | 80%+ | ~30 tests |

### Backend Breakdown:
- analytics_service.py: 16% → 90%
- rate_limiter.py: 0% → 90%
- deletion_request_service.py: 18% → 85%
- activity_log_service.py: 33% → 90%
- gmail_service.py: 17% → 75%
- gemini_service.py: 22% → 80%
- email_scanner.py: 8% → 70%
- response_matcher.py: 22% → 80%
- API routes: 20-40% → 75-85%
- email_tasks.py: 11% → 60%

### Frontend Breakdown:
- api.ts: 37% → 85%
- hooks: Add 5 new test files for missing hooks

---

## Critical Files to Modify

### Backend:
- `backend/pyproject.toml` - add dev dependencies
- `backend/tests/conftest.py` - add new fixtures

### Frontend:
- `frontend/src/test/mocks/handlers.ts` - may need additional handlers
- `frontend/src/services/__tests__/api.test.ts` - new file

---

## Risk Areas

1. **Gmail Service**: Complex OAuth mocking, may need integration test approach
2. **Celery Tasks**: Task testing requires special setup, may settle for 60% coverage
3. **Email Scanner**: Many edge cases, focus on main happy paths first
