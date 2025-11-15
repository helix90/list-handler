# Production Authentication Issue - Debug Guide

## Problem Summary
Client can:
- ✅ Login successfully
- ✅ List existing lists (GET request)
- ❌ Create a new list (POST request) - returns 401 Unauthorized

## Test Results
All integration tests **PASS** in the test environment, including:
- `test_full_authentication_flow_across_endpoints` - Tests login → list → create
- `test_token_consistency_across_methods` - Tests GET, POST, PUT, DELETE with same token
- `test_login_then_immediate_post` - Tests exact failing sequence

**Conclusion**: The issue is **environment-specific** to production.

## Most Likely Causes

### 1. **Different SECRET_KEY Between Environments** ⚠️ HIGH PRIORITY
**Symptoms**: Token works for some endpoints but not others
**Root Cause**: If production has a different `SECRET_KEY` than what was used to generate the token, JWT validation will fail randomly or consistently.

**How to check**:
```bash
# In production container/server
echo $SECRET_KEY

# Compare with docker-compose.yml
grep SECRET_KEY docker-compose.yml
```

**Fix**: Ensure `SECRET_KEY` is consistent across all services and deployments.

### 2. **Reverse Proxy/Load Balancer Stripping Headers**
**Symptoms**: GET requests work, POST requests fail
**Root Cause**: Some proxies handle GET and POST differently, especially with custom headers like `Authorization`.

**Common culprits**:
- Nginx not forwarding Authorization header for POST
- Apache with `RewriteRule` stripping headers
- AWS ALB/ELB with specific security groups
- Cloudflare or other CDN with security rules

**How to check**:
```bash
# Check nginx config for:
proxy_set_header Authorization $http_authorization;
proxy_pass_header Authorization;

# Or check if headers are being stripped:
curl -X POST https://production-url/users/1/lists \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test"}' \
  -v  # Verbose mode shows all headers
```

**Fix**: Add proper header forwarding in your reverse proxy config.

### 3. **CORS Preflight Request Issues**
**Symptoms**: Works in tests, fails in browser/certain clients
**Root Cause**: Browsers send OPTIONS request before POST with custom headers. If preflight fails, POST is never sent.

**How to check**:
- Open browser Developer Tools → Network tab
- Look for OPTIONS request before POST
- Check if OPTIONS returns 200 and proper CORS headers

**Fix**: Ensure CORS middleware allows Authorization header:
```python
# Already configured correctly in main.py:
allow_headers=["*"]
allow_methods=["*"]
```

But if there's a reverse proxy, it might need CORS config too.

### 4. **Database Connection Pool Exhaustion**
**Symptoms**: GET requests (read-only) work, POST requests (write) fail
**Root Cause**: Database connection issues affect write operations more than reads.

**How to check**:
```bash
# Check application logs for database errors
docker logs list-handler-api | grep -i "database\|connection"

# Check SQLite database
ls -la data/list_handler.db
# Ensure proper permissions (should be writable)
```

**Fix**: Check database file permissions and connection handling.

### 5. **Token Expiry/Clock Skew**
**Symptoms**: Token seems valid but authentication fails intermittently
**Root Cause**: System clocks are out of sync between services

**How to check**:
```bash
# Check system time on production
date
timedatectl

# Decode JWT token to check expiry
# Use https://jwt.io or:
python3 -c "import jwt; import sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))" "YOUR_TOKEN"
```

**Fix**: Synchronize system clocks using NTP.

### 6. **Different Python/Dependency Versions**
**Symptoms**: Inconsistent behavior between environments
**Root Cause**: Different versions of `python-jose`, `passlib`, or `fastapi`

**How to check**:
```bash
# In production
pip list | grep -E "fastapi|jose|passlib"

# Compare with requirements.txt
cat requirements.txt
```

## Debugging Steps

### Step 1: Enable Detailed Logging

Add this to your production `main.py` temporarily:

```python
import logging

# Add at the top of main.py
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger = logging.getLogger("api")
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
```

### Step 2: Test Directly Against Container

Bypass any reverse proxy:

```bash
# SSH into production server
# Get the exact token from a successful login
TOKEN=$(curl -X POST http://localhost:8088/auth/login \
  -d "username=testuser&password=testpass" | jq -r '.access_token')

echo "Token: $TOKEN"

# Test GET (should work)
curl -X GET http://localhost:8088/users/1/lists \
  -H "Authorization: Bearer $TOKEN" \
  -v

# Test POST (check if it works directly)
curl -X POST http://localhost:8088/users/1/lists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Direct Test"}' \
  -v
```

If POST works directly but fails through the proxy → **Issue is in the reverse proxy**

If POST fails even directly → **Issue is in the application/environment**

### Step 3: Compare JWT Tokens

```bash
# Decode token from production
python3 << EOF
import jwt
import sys

token = "YOUR_PRODUCTION_TOKEN"
try:
    # Don't verify signature, just decode
    payload = jwt.decode(token, options={"verify_signature": False})
    print("Token payload:", payload)
    print("Token algorithm:", jwt.get_unverified_header(token))
except Exception as e:
    print(f"Error: {e}")
EOF
```

Check:
- `exp` (expiration) - should be in the future
- `sub` (subject) - should be the username
- Algorithm should be `HS256`

### Step 4: Check Environment Variables

```bash
# In production container
docker exec list-handler-api env | grep -E "SECRET|DATABASE|ALGORITHM"
```

### Step 5: Monitor Real Requests

Add this to `app/auth.py` temporarily:

```python
# In get_current_user function, add debug logging
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    import logging
    logger = logging.getLogger("auth")
    logger.info(f"Received token: {token[:20]}...")  # Log first 20 chars
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        logger.info(f"Token decoded successfully: {payload}")
        username: str = payload.get("sub")
        if username is None:
            logger.error("No 'sub' in token payload")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.error(f"User not found: {username}")
        raise credentials_exception
    logger.info(f"User authenticated: {user.username}")
    return user
```

## Quick Fixes to Try

### Fix #1: Ensure Consistent SECRET_KEY
```bash
# Set in environment
export SECRET_KEY="your-production-secret-key"

# Or in docker-compose.yml
environment:
  - SECRET_KEY=your-production-secret-key-here-make-it-long-and-random
```

### Fix #2: Add Nginx Config (if using Nginx)
```nginx
location /api/ {
    proxy_pass http://localhost:8088/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Authorization $http_authorization;  # Important!
    proxy_pass_header Authorization;  # Important!
}
```

### Fix #3: Check File Permissions
```bash
# Ensure database is writable
chmod 666 data/list_handler.db
chmod 777 data/
```

## Testing the Fix

After applying a fix, run this sequence:

```bash
# 1. Login
curl -X POST https://your-production-url/auth/login \
  -d "username=USER&password=PASS" \
  -o token.json

# 2. Extract token
TOKEN=$(cat token.json | jq -r '.access_token')

# 3. Test GET
curl -X GET "https://your-production-url/users/USER_ID/lists" \
  -H "Authorization: Bearer $TOKEN"

# 4. Test POST (this should now work)
curl -X POST "https://your-production-url/users/USER_ID/lists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production Test List"}'
```

## Prevention - Run Integration Tests in CI/CD

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml or similar
test:
  steps:
    - name: Run integration tests
      run: |
        python -m pytest tests/test_integration.py -v
    - name: Test with production-like environment
      run: |
        docker-compose -f docker-compose.prod.yml up -d
        sleep 10
        pytest tests/test_integration.py --base-url=http://localhost:8088
```

## Contact Information
If issue persists after trying all above:
1. Collect logs with debug logging enabled
2. Compare test environment vs production environment variables
3. Check if issue is client-specific (browser vs curl vs mobile app)

---
**Created**: For debugging production authentication issue where login + GET works but login + POST fails with 401

