# Password Reset Policy

**Document owner:** IT Security Team
**Last updated:** 2026-02-01
**Applies to:** All employees, contractors, and interns with a corporate account

## Overview

This policy describes how employees can reset forgotten or expired passwords for
their corporate identity (Okta Single Sign-On), and the rules governing password
strength, rotation, and account lockouts.

## Self-Service Password Reset

Most employees can reset their own password without contacting IT:

1. Go to the Okta sign-in page and click "Forgot Password."
2. Verify your identity via the MFA method on file (Okta Verify push, SMS backup
   code, or security questions if enrolled).
3. Choose a new password that meets the complexity requirements below.
4. Your new password propagates to email, VPN, and internal apps within 5 minutes.

If self-service reset fails three times, your account is temporarily locked for
15 minutes as a brute-force protection measure.

## When to Contact the IT Help Desk

Submit a "Password Reset" ticket through MiniDesk IQ if:

- You no longer have access to your MFA device and cannot verify identity.
- Your account shows as locked for longer than 15 minutes.
- You suspect your account has been compromised (in this case, also notify
  Security immediately at security@company.com).
- You are a new hire whose temporary password has expired before first login.

Help desk password resets require a live identity check (manager confirmation or
video call with camera on) before a temporary password is issued.

## Password Complexity Requirements

- Minimum 14 characters.
- Must include at least one uppercase letter, one lowercase letter, one number,
  and one special character.
- Cannot reuse any of your last 10 passwords.
- Cannot contain your username, first name, or last name.
- Passphrases (e.g., four random words) are encouraged and count toward length.

## Rotation Policy

- Standard employee accounts: passwords expire every 180 days.
- Privileged/admin accounts (IT, Security, Finance system admins): passwords
  expire every 90 days.
- Service accounts: passwords are rotated automatically by the secrets manager
  and are not user-managed.

## Account Lockout Rules

- 5 failed login attempts within 10 minutes triggers a 30-minute lockout.
- 10 failed attempts in 24 hours flags the account for a manual Security review
  and requires help desk-assisted unlock.

## Shared Accounts

Shared or generic accounts (e.g., conference room kiosks) are prohibited except
where explicitly approved by IT Security, and must use a managed password rotated
monthly by the system administrator.

## Related Policies

- VPN Access Policy
- Remote Work Policy
