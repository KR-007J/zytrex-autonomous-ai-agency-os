# LeadForge — Security & DevSecOps Specification

## 1. SSRF (Server-Side Request Forgery) Protection
LeadForge crawls arbitrary external domain names. To prevent internal network scanning and cloud metadata theft, every network operation passes through `src/security/ssrf.py`:
- **Blocked CIDRs**:
  - `127.0.0.0/8` (Loopback)
  - `10.0.0.0/8` (RFC 1918 Private)
  - `172.16.0.0/12` (RFC 1918 Private)
  - `192.168.0.0/16` (RFC 1918 Private)
  - `169.254.0.0/16` (Link-Local & Cloud Metadata `169.254.169.254`)
  - `0.0.0.0/8`
  - `::1/128`, `fc00::/7`, `fe80::/10`
- **DNS Rebinding Defense**:
  - Validates resolved IP addresses before establishing TCP handshakes.
  - Re-checks final destination on HTTP redirect chains.
- **Allowed Schemes**: Only `http` and `https`.

## 2. Responsible Crawling & Politeness
- Honors `robots.txt` disallow directives.
- Uses identifiable User-Agent (`LeadForgeBot/2.0`).
- Strict connection timeouts (default 10s) and per-domain concurrency limits.
- Never bypasses CAPTCHA, authentication, paywalls, or access controls.

## 3. API Key Security
- API keys are generated using cryptographically secure tokens (`secrets.token_urlsafe(32)`).
- Keys are hashed with SHA-256 before storage; raw keys are never persisted in the database.
- Key revocation and rotation supported out-of-the-box.
