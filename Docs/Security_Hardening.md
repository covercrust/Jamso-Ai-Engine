# Security Hardening Checklist for Jamso AI Engine

## 1. Environment & Secrets
- [x] All secrets and credentials are loaded from environment variables or env.sh (never hardcoded).
- [x] `.gitignore` excludes all sensitive files (env.sh, *.key, *.token, etc).
- [x] Use strong, unique secrets for all API keys and tokens.
- [ ] Consider using a secrets manager for production (AWS, Azure, Vault, etc).

## 2. Dependencies
- [x] All dependencies are pinned in requirements.txt.
- [x] Unused or deprecated requirements are removed.
- [x] Use `pip-audit` or `safety` to check for vulnerabilities regularly.

## 3. Docker & Deployment
- [x] Dockerfile uses a non-root user.
- [x] Only necessary ports are exposed.
- [x] Multi-stage builds to reduce image size.
- [ ] Enable image scanning in CI/CD.

## 4. Application
- [x] CSRF protection enabled (Flask-WTF, Dashboard).
- [x] Session cookies are secure and HTTPOnly.
- [x] All user input is validated and sanitized.
- [x] Logging does not leak sensitive data.

## 5. Monitoring
- [x] Log rotation is enabled.
- [x] Monitor for suspicious activity in logs.

---

**Review this checklist before every deployment!**
