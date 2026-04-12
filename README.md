# # COMP-3297-2026-group-D BetaTrax Sprint 2

## Project Overview
BetaTrax is a defect tracking system developed using **Django 6.0.2** and **Django Rest Framework (DRF)**.


## Sprint 2 Enhancements over Sprint 1
- ✅ Product Owner can assign multiple developers when registering a product – Only developers who are not already assigned to another product are available for selection. A developer cannot be responsible for more than one product at a time.
- ✅ Restricted status transitions for Product Owner and Developer – State changes follow strict business rules:
  -Product Owner can only change: new → open, rejected, duplicate; fixed → reopened, resolved.
  -Developer can only change: open / reopened → assigned; assigned → fixed, cannot_reproduce.
- ✅ Duplicate defect handling with email merging – When a Product Owner marks a defect as duplicate, they must provide a target_defect_id. The current defect’s tester email(s) are merged into the target defect’s tester email list. As a result, when the target defect’s status changes, all testers (including those from the duplicate) receive notifications.
- ✅ Full comment system for Product Owners and Developers – Both roles can add comments to any defect they have access to. Each comment includes author, timestamp, and text, and is automatically assigned a unique comment ID.
- ✅ Automatic email notifications on every status change – Whenever a defect’s status changes, an email is sent to all email addresses listed in the defect’s tester_email field (supports multiple comma‑separated emails).
- ✅ Auto‑generated User ID for each new user – When an administrator creates a user account, a unique user ID is automatically generated and stored (in addition to the default id field).
- ✅ Filtering functionality – Product Owners and Developers can filter defect reports related to their own products using custom filters (e.g., by status, severity, priority, or date).
- ✅ Role‑based restrictions on actions:
  -Testers can submit defect reports but cannot register products.
  -Developers can modify defects but cannot register products.
  -Product Owners can register products but cannot submit defect reports.

## How to Run
1. Activate virtual environment: run `python -m venv venv` and then run `.\venv\Scripts\activate` and then run `pip install Django==6.0.2 djangorestframework django-filter`
2. Run the server: `python manage.py runserver`
3. Admin panel: http://127.0.0.1:8000/admin/  
4. API endpoint: http://127.0.0.1:8000/api/defects/ -->this one for developers and owners to review the reports
                 http://127.0.0.1:8000/api/products/ -->this one for owners to add new products
5. View defect reports: Open http://127.0.0.1:8000/api/defects/<id>/ (e.g., http://127.0.0.1:8000/api/defects/1/) in your browser after logging in.
6. View products: Open http://127.0.0.1:8000/api/products/<id>/ (e.g., http://127.0.0.1:8000/api/products/1/) in your browser after logging in.
## Limitations (Sprint 2)
- Email notifications rely on a console backend in development
- Comment system does not support editing or deleting comments
- User groups must be manually created via Admin


---
