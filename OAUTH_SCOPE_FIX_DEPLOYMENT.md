# OAuth Scope Fix - Production Deployment Guide

## Problem

Users are getting `403 Insufficient Permission` errors when scanning emails because their OAuth tokens don't have the required `gmail.readonly` scope.

### Root Cause

1. The code had `OAUTHLIB_RELAX_TOKEN_SCOPE = "1"` set, which allowed Google to issue tokens WITHOUT the requested scopes
2. When users authenticated, Google sometimes didn't grant `gmail.readonly` scope
3. The application accepted these insufficient tokens and stored them
4. When trying to read Gmail, the API returns 403 because the token lacks the required scope

## The Fix

Three code changes have been made:

1. **Disabled `OAUTHLIB_RELAX_TOKEN_SCOPE`** in `backend/app/services/gmail_service.py`
   - Prevents accepting tokens without required scopes

2. **Added scope validation** in `backend/app/api/auth.py`
   - OAuth callback now validates that ALL required scopes were granted
   - Rejects authentication if any scope is missing

3. **Enhanced authorization URL** in `backend/app/services/gmail_service.py`
   - Added `include_granted_scopes="false"` to prevent incremental auth issues
   - Always shows full consent screen with `prompt="consent"`

4. **Created migration** `c8ada720b72d_force_oauth_reauth_for_scope_fix.py`
   - Clears all existing OAuth tokens
   - Forces all users to re-authenticate with proper scopes

## Deployment Steps

### Step 1: Verify Google Cloud Console Configuration

Before deploying, ensure OAuth scopes are correctly configured in Google Cloud Console:

1. Go to **APIs & Services** → **OAuth consent screen**
2. Click **"EDIT APP"**
3. Scroll to **"Scopes"** section
4. Verify these 4 scopes are configured:
   - ✅ `openid`
   - ✅ `https://www.googleapis.com/auth/userinfo.email`
   - ✅ `https://www.googleapis.com/auth/gmail.readonly`
   - ✅ `https://www.googleapis.com/auth/gmail.send`
5. **Remove any other scopes** that are not in this list
6. Save changes

### Step 2: Deploy Code Changes

```bash
# On production server
cd ~/OpenShred

# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker compose down
docker compose up -d --build

# Check that services started successfully
docker compose ps
docker compose logs backend --tail=50
docker compose logs celery-worker --tail=50
```

### Step 3: Run Database Migration

The migration will automatically run on backend startup via the entrypoint script. Verify it ran:

```bash
# Check migration logs
docker compose logs backend | grep "Running upgrade"

# Should see:
# INFO  [alembic.runtime.migration] Running upgrade c3f7d9a2a1e4 -> c8ada720b72d, force_oauth_reauth_for_scope_fix
```

### Step 4: Verify Migration Completed

```bash
# Connect to database
docker compose exec db psql -U openshred -d openshred

# Check current migration version
# (Inside psql)
SELECT version_num FROM alembic_version;
# Should show: c8ada720b72d

# Verify tokens were cleared
SELECT COUNT(*) FROM users WHERE google_access_token IS NOT NULL;
# Should show: 0

# Exit psql
\q
```

### Step 5: Manual Token Clear (Alternative)

If the migration doesn't run automatically, you can manually clear tokens:

```bash
# Connect to database
docker compose exec db psql -U openshred -d openshred

# Clear all OAuth tokens
UPDATE users
SET google_access_token = NULL,
    google_refresh_token = NULL
WHERE google_access_token IS NOT NULL;

# Verify
SELECT id, email, google_access_token IS NULL as token_cleared FROM users;

# Exit
\q
```

### Step 6: Notify Users

After deployment, ALL users will need to:

1. **Log out** of the application (if currently logged in)
2. **Log back in** via Google OAuth
3. **Accept ALL permissions** when Google shows the consent screen
   - Make sure they grant permission for "Read email" (gmail.readonly)
   - If they decline any permission, authentication will fail with a clear error message

## Verification

### Test Authentication Flow

1. Clear your browser cookies for the application domain
2. Visit the login page
3. Click "Sign in with Google"
4. Google should show consent screen with these permissions:
   - Know who you are on Google
   - See your primary Google Account email address
   - **Read all resources and their metadata—no write operations (Gmail)**
   - Send email on your behalf
5. Accept all permissions
6. You should be redirected back and successfully logged in

### Test Email Scanning

1. After logging in, go to Email Scans page
2. Click "Scan Inbox"
3. Scan should complete successfully without 403 errors
4. Check backend logs for confirmation:
   ```bash
   docker compose logs backend --tail=100 | grep "403"
   # Should see no recent 403 errors after re-authentication
   ```

## Rollback Plan

If something goes wrong:

```bash
# Rollback to previous version
cd ~/OpenShred
git reset --hard HEAD~1

# Rebuild containers
docker compose down
docker compose up -d --build

# Rollback migration (if needed)
docker compose exec backend alembic downgrade -1
```

Note: Rollback won't restore user tokens - users will still need to re-authenticate.

## Common Issues

### Issue: Users still getting 403 after re-authenticating

**Cause**: Google OAuth might be using cached consent if user recently granted some scopes.

**Solution**:
1. Have user completely sign out of their Google account
2. Sign back into Google account
3. Then authenticate with the application
4. This forces Google to show fresh consent screen

### Issue: Authentication fails with "Missing required OAuth scopes"

**Cause**: User declined one or more permissions during consent screen.

**Solution**:
1. User needs to re-authenticate
2. Make sure they **accept ALL permissions** when Google shows consent screen
3. If they're uncomfortable granting email read permission, they cannot use the application

### Issue: Migration shows as applied but tokens not cleared

**Cause**: Migration might have run before, or manual intervention needed.

**Solution**: Run the manual SQL from Step 5 above.

## Post-Deployment Monitoring

Monitor logs for the first hour after deployment:

```bash
# Watch for 403 errors
docker compose logs -f backend celery-worker | grep -i "403\|insufficient"

# Watch for successful scans
docker compose logs -f celery-worker | grep "scan_inbox_task.*succeeded"
```

Expected behavior:
- **Before re-auth**: 403 errors for users with old tokens
- **After re-auth**: Scans complete successfully with no permission errors

## Security Notes

This fix improves security by:
1. **Enforcing scope validation** - Application will reject tokens without required permissions
2. **Preventing silent failures** - Clear error messages when permissions are missing
3. **Explicit consent** - Users must explicitly grant email read permission
4. **No relaxed validation** - OAuth library will strictly validate scopes

## Support

If users report issues after deployment:

1. **Check their error message** - Should clearly indicate if missing scopes
2. **Verify Google Cloud Console** - Ensure all 4 scopes are configured
3. **Check backend logs** - Look for scope validation errors
4. **Have them try incognito mode** - Rules out browser cache issues
5. **Verify database** - Check if their tokens were properly cleared

---

**Deployed on**: _[Fill in deployment date]_
**Deployed by**: _[Fill in your name]_
**Verified by**: _[Fill in tester name]_
