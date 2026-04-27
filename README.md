# # COMP-3297-2026-group-D BetaTrax Sprint 3

## Project Overview
BetaTrax is a defect tracking system developed using **Django 6.0.2** and **Django Rest Framework (DRF)**.

For submission-ready API documentation, see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).


## Sprint 3 Enhancements over Sprint 1 & 2
- **Multi-tenant support** – Added tenant isolation to enable BetaTrax to be rolled out as a SaaS product for other development companies, as described in the Project Description.

- **Developer effectiveness metric** – Implemented a simple metric to calculate and report the effectiveness of individual developers in fixing defects.

- **Basic automated tests** – Added a suite of basic automated tests for the Django web service, covering models, forms, and key API endpoints.

- **Tests + coverage for developer effectiveness classification** – Wrote dedicated tests for the code that classifies developer effectiveness, and used a coverage tool to demonstrate that those tests meet specified adequacy criteria .

- **User ID visibility & API usage** – Each user's User ID is now visible in the admin system. When requesting the effectiveness metric for a particular developer, the API expects the developer's User ID to be provided as a parameter.

- **Fixed email notification issue** – Resolved the problem from Sprint 2 where notification emails were not actually being sent.

- **Fixed duplicate notification issue** – Resolved the problem where tester_email merging was incorrectly treated the same as cascade notifications; they are now handled separately.


## How to Run
1. Activate virtual environment: run `python -m venv venv` (or `python3 -m venv venv` for MacOS and Linux) and then run `.\venv\Scripts\activate` (or `. venv/bin/activate` for MacOS and Linux) and then run `pip install Django==6.0.2 djangorestframework django-filter`. Lastly, run `pip install -r requirements.txt` to ensure all required files are installed.
2. Run the server: `python manage.py runserver`
3. Root URL: http://127.0.0.1:8000/ now redirects to the API landing page at http://127.0.0.1:8000/api/  
4. Admin panel: http://127.0.0.1:8000/admin/  
5. API endpoint: http://127.0.0.1:8000/api/defects/ -->this one for developers and owners to review the reports
                 http://127.0.0.1:8000/api/products/ -->this one for owners to add new products
6. View defect reports: Open http://127.0.0.1:8000/api/defects/<id>/ (e.g., http://127.0.0.1:8000/api/defects/1/) in your browser after logging in.
7. View products: Open http://127.0.0.1:8000/api/products/<id>/ (e.g., http://127.0.0.1:8000/api/products/1/) in your browser after logging in.
8. View developer metrics: Open http://127.0.0.1:8000/api/defects/metrics/<user_id>/ (e.g., http://127.0.0.1:8000/api/defects/metrics/12/) in your browser after logging in (The user_id here must be a the id of a developer).

## Automation Test Instructions (Sprint 3)
**Preconditions:**
1) python/python3 intsalled
2) have coverage installed (run `pip install coverage` to install coverage)

**Run Instructions(API Test):**
1) Do [How to Run](#How-to-Run) Step 1 & 2
2) Run `python manage.py test defects.test_api`

**Run Instructions(Developer Metrics Classification Logic Test):**
1) Do [How to Run](#How-to-Run) Step 1 & 2
1) Run "python manage.py test defects.test_dev_metrics" for normal testing

**Generate Coverage Report (Developer Metrics Classification Logic Test):**
1) run `coverage run --source='defects' manage.py test defects.test_dev_metrics`
2) run `coverage report --include="views.py"` to generate report
3) run `coverage report -m --include="view.py"` to see how many line the testing misses
4) run `coverage html --include="views.py"` to generate the report in html
5) run "open htmlcov/index.html" / "xdg-open htmlcov/index.html" / "start htmlcov/index.html" to view report in MacOS / Linux / Windows
'''


## Limitations (Sprint 3)






---
