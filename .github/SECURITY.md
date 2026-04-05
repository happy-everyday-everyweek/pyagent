# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.8.x   | :white_check_mark: |
| 0.7.x   | :white_check_mark: |
| < 0.7   | :x:                |

## Reporting a Vulnerability

We take the security of PyAgent seriously. If you have discovered a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security Advisories](https://github.com/your-org/pyagent/security/advisories) page
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email**
   - Send an email to: security@pyagent.ai
   - Include "SECURITY" in the subject line

### What to Include

Please include the following information:

- Type of vulnerability
- Full path of source file(s) related to the vulnerability
- Steps to reproduce
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Depends on severity and complexity

### Disclosure Policy

- We follow responsible disclosure
- We will credit you for the discovery (unless you prefer to remain anonymous)
- We request that you do not disclose the vulnerability publicly until a fix is released

## Security Best Practices

When using PyAgent, please follow these security best practices:

### API Keys and Secrets

- Never hardcode API keys in your code
- Use environment variables or secure secret management
- Rotate keys regularly
- Use the virtual key management feature for production deployments

### Data Privacy

- Be aware of what data is sent to LLM providers
- Review and configure memory retention policies
- Use local models when handling sensitive data

### Network Security

- Use HTTPS for all external communications
- Configure firewall rules appropriately
- Keep dependencies up to date

### Access Control

- Use the permission system to restrict access
- Implement proper authentication for web interfaces
- Review and audit access logs regularly

## Security Features

PyAgent includes several security features:

- **Virtual Key Management**: Secure API key handling
- **Permission System**: Role-based access control
- **Audit Logging**: Track system activities
- **Data Encryption**: Encrypt sensitive data at rest

## Security Updates

Security updates are released as patch versions and are announced via:

- GitHub Security Advisories
- Release notes
- CHANGELOG.md

We recommend updating to the latest version promptly when security updates are released.

## Third-Party Dependencies

We regularly audit our dependencies for known vulnerabilities. If you discover a vulnerability in a dependency, please report it to us and we will work to update or replace the affected dependency.

## Contact

For general security questions (non-vulnerability reports):

- Open a GitHub Discussion
- Email: security@pyagent.ai

Thank you for helping keep PyAgent secure!
