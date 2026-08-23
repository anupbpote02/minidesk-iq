# VPN Access Policy

**Document owner:** IT Security Team
**Last updated:** 2026-01-15
**Applies to:** All full-time employees, contractors, and interns

## Overview

The company VPN (Virtual Private Network) provides secure, encrypted access to internal
systems, file shares, and applications when working outside of a corporate office network.
All remote connections to internal resources must go through the approved VPN client.

## Who Is Eligible

- Full-time employees are eligible for VPN access by default once their IT onboarding
  ticket is completed.
- Contractors and interns require manager approval before VPN access is provisioned.
- Third-party vendors must submit a Vendor Access Request and are subject to a 90-day
  access review cycle.

## How to Request VPN Access

1. Submit a VPN Access request through MiniDesk IQ or the IT self-service portal.
2. Include your manager's name and the business justification for remote access.
3. IT Security reviews requests within 1 business day for employees, and up to
   3 business days for contractors and vendors pending manager sign-off.
4. Once approved, you will receive setup instructions and a client configuration
   file via your corporate email within 4 business hours.

## Approved VPN Client

The company uses **GlobalProtect** as its standard VPN client. Do not use personal or
third-party VPN software to connect to corporate resources — unauthorized VPN clients
are blocked at the network firewall and may trigger a security incident review.

## Multi-Factor Authentication (MFA)

VPN connections require MFA on every login. Approved MFA methods are:

- Push notification via the Okta Verify mobile app (recommended)
- Time-based one-time password (TOTP) from Okta Verify
- Hardware security key (YubiKey) for employees enrolled in the high-security group

If you lose access to your MFA device, contact the IT help desk immediately to have
your MFA re-enrolled after identity verification.

## Session and Timeout Rules

- VPN sessions automatically time out after 45 minutes of inactivity.
- Maximum continuous session length is 12 hours, after which re-authentication is
  required.
- Split tunneling is disabled by default; all traffic routes through the corporate
  network while connected.

## Revocation

VPN access is automatically revoked when:

- An employee's employment ends (processed same-day by IT during offboarding).
- A contractor's engagement end date passes without a renewal request.
- Security flags unusual login activity (e.g., simultaneous logins from two countries),
  pending manual review.

## Troubleshooting

If you cannot connect:

1. Confirm you are using the latest GlobalProtect client version.
2. Verify your corporate credentials have not expired (see Password Reset Policy).
3. Check the IT status page for any active outages.
4. If the issue persists, open a ticket with category "VPN Access" including your
   OS version, client version, and any error codes shown.

## Related Policies

- Remote Work Policy
- Password Reset Policy
