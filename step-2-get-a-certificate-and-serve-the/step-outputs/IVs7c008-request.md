# Request — Design the approach and write the implementation plan

Task: https://trello.com/c/IVs7c008 (id 6ab523bfa0e4fe24df0a8d48)
Step: https://trello.com/c/RbsRQzYp — Step 2: Get a certificate and serve the site over HTTPS
Received: 2026-09-24

## Ask, as received

www.f3lcontestseries.org is served over plain HTTP today, and the pages link to themselves with http:// URLs. Goal: obtain a TLS certificate (Let's Encrypt if the host supports it) and offer the site over HTTPS, then make the site's own links and any canonical URLs use https://, with HTTP redirecting to HTTPS if the host allows it.

The design must first establish what the hosting provider behind ftp.mcneilco.com offers (control panel, AutoSSL / Let's Encrypt, where the certificate is installed, whether renewal is automatic) — that is where the real work is, and most of it needs John's access to the hosting account, so tag those items [needs-you]. The site-side changes (links, redirects via .htaccess or equivalent) are ordinary implementation items deployed with the Step 0 system.

Step checklist at launch: this item, then `Confirm the hosting provider and control-panel access for www.f3lcontestseries.org and note which certificate options it offers [needs-you]`. No comments, no attachments.

This task's own scope: write the spec, design and implementation plan; derive the implementation tasks for the step checklist.
