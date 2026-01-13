# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please email the maintainers directly. Do not open a public issue.

## Security Measures Implemented

### 1. **CORS Protection**
- Strict origin validation
- No wildcards allowed in production
- Must explicitly define allowed origins in `.env`

### 2. **Rate Limiting**
- Per-IP rate limiting (default: 100 requests/60 seconds)
- Configurable via environment variables
- Prevents brute force and DoS attacks

### 3. **Security Headers**
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection` - XSS protection
- `Strict-Transport-Security` - HTTPS enforcement (production only)
- `Content-Security-Policy` - Restricts resource loading

### 4. **Input Validation**
- All user inputs are validated
- Maximum value limits enforced
- Type checking on all parameters
- Length limits on string fields

### 5. **Error Handling**
- Generic error messages in production
- Detailed errors only in development
- No sensitive information in error responses
- All errors logged securely

### 6. **Environment Configuration**
- Separate dev/production configurations
- Required environment variables validation at startup
- Credentials file validation
- No hardcoded secrets

### 7. **API Documentation**
- Swagger/Redoc disabled in production
- Only available in development mode

### 8. **Trusted Host Protection**
- Host header validation in production
- Prevents host header injection attacks

## Best Practices for Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure specific `CORS_ORIGINS` (no wildcards!)
- [ ] Set `ALLOWED_HOSTS` for your domain
- [ ] Use HTTPS only
- [ ] Protect `credentials.json` file (never commit!)
- [ ] Use strong Telegram bot token
- [ ] Restrict Google Sheets access
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Implement backup strategy

### Environment Variables Required

```bash
# Required
TELEGRAM_TOKEN=xxx
SPREADSHEET_ID=xxx
GOOGLE_CREDENTIALS_FILE=credentials.json

# Recommended for Production
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=60
```

## Security Considerations

### Google Sheets Access
- Use Service Account with minimum required permissions
- Only grant "Editor" access to specific spreadsheet
- Never share service account JSON publicly
- Rotate credentials periodically

### Telegram Bot
- Keep bot token secret
- Never commit `.env` file
- Use bot commands authentication if needed
- Consider user whitelisting for production

### API Endpoints
- All endpoints use caching to prevent excessive Sheets API calls
- Rate limiting applies to all endpoints
- Input validation on all parameters

## Updates

Security updates are released as needed. Check GitHub releases for security patches.

## License

This security policy is part of the Finance Tracker Bot project.
