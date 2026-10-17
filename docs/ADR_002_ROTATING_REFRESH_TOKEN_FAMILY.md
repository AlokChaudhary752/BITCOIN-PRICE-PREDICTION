# ADR 002: Rotating Refresh Token Families and Reuse Revocation

## Status
Accepted

## Context
Web applications storing long-lived JWTs or session identifiers in `localStorage` or `sessionStorage` are vulnerable to Cross-Site Scripting (XSS) extraction attacks. Conversely, relying solely on static refresh tokens without rotation exposes users to persistent replay attacks if a refresh token is intercepted.

## Decision
We implemented **Rotating Refresh Token Families** combined with strict cookie encapsulation:
1. **Cookie Configuration:** The refresh token is delivered in an `httpOnly`, `Secure`, `SameSite=Strict` cookie (`btc_oracle_refresh`). JavaScript cannot read or extract this cookie.
2. **Access Token Lifespan:** Short 15-minute expiration passed strictly in memory / Authorization headers.
3. **Token Rotation & Family Tree:** Each refresh request generates a cryptographic random token string and immediately invalidates the previous token, assigning a shared `family_id`.
4. **Automatic Reuse Revocation:** If an invalidated token from a family is submitted again, the system identifies this as token theft / replay and immediately revokes all tokens belonging to that `family_id`, forcing an immediate re-authentication and logging an audit event.
5. **Progressive Lockout:** Failed authentication attempts trigger a 15-minute lockout upon 5 consecutive failures.

## Consequences
- **Positive:** XSS attacks cannot exfiltrate long-lived refresh credentials.
- **Positive:** Stolen refresh tokens are instantly rendered useless upon legitimate user token rotation, and any replay triggers instant revocation of the compromised session.
- **Positive:** Full compliance with OAuth 2.0 Security Best Current Practice (BCP RFC 6749 / 6819).
