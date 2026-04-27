# BetaTrax API Documentation

## Overview

BetaTrax is a role-based defect tracking API built with Django and Django REST Framework. The API uses session authentication, Django groups for authorization, and a small set of custom actions for duplicate handling, status workflow discovery, and developer metrics.

The documentation below reflects the implemented behavior in the codebase, not only the original README text. Where the README and implementation differ, this document follows the code and tests.

## Base URL and Authentication

- Base URL: `/api/`
- Authentication: Django session authentication via `/api-auth/login/`
- Default permission: authenticated users only
- Roles used by the API:
  - `Tester`
  - `Developer`
  - `Product Owner`

Users are assigned to roles through Django groups. A user can belong to more than one group, but the implemented checks usually branch on the first matching role-specific condition.

## API Summary

| Path | Methods | Role access | Purpose |
|---|---|---|---|
| `/api/defects/` | `GET`, `POST` | Authenticated; create is Tester only | List defects visible to the current user, or create a defect report |
| `/api/defects/{id}/` | `GET`, `PUT`, `PATCH`, `DELETE` | Authenticated; updates are limited by product ownership or product developer membership | Retrieve, update, or delete a defect |
| `/api/defects/{id}/candidate-targets/` | `GET` | Authenticated | List valid duplicate targets in the same product |
| `/api/defects/{id}/allowed-statuses/` | `GET` | Authenticated | Show allowed next statuses for the current user on a defect |
| `/api/defects/metrics/{user_id}/` | `GET` | Authenticated | Return a developer rating from defect history |
| `/api/products/` | `GET`, `POST` | Authenticated; create is Product Owner only | List or create products |
| `/api/products/{id}/` | `GET`, `PUT`, `PATCH`, `DELETE` | Authenticated; access effectively limited to the owning Product Owner | Retrieve, update, or delete a product |

## Data Model Reference

### Product

Fields exposed by the serializer:

- `id`: integer, read-only
- `product_id`: string, max length 50, required
- `version`: string, max length 20, required
- `owner`: string, read-only, automatically assigned from the current user
- `description`: string, optional
- `developers`: array of user IDs, optional
- `expiry_date`: date, optional
- `created_at`: timestamp, read-only

Important behavior:

- The pair `(product_id, version)` is unique.
- Each assigned developer can belong to only one product.
- `product_id` is the user-facing product name even though the field name looks like an identifier.

### Defect

Fields exposed by the serializer:

- `id`: integer, read-only
- `product`: integer foreign key to Product, required
- `title`: string, max length 200, required
- `description`: string, required
- `steps_to_reproduce`: string, optional
- `tester_id`: string, read-only, populated from the authenticated user ID
- `tester_email`: string, optional input field, stored as text and used for notifications
- `duplicate_of`: integer foreign key to another defect, read-only in the API response
- `severity`: string choice, default `medium` in the model, with allowed values `low`, `minor`, `major`, `critical`
- `priority`: string choice, default `medium` in the model, with allowed values `low`, `medium`, `high`, `critical`
- `status`: string choice, default `new`, with allowed values `new`, `open`, `rejected`, `assigned`, `fixed`, `reopened`, `resolved`, `duplicate`, `cannot_reproduce`
- `assigned_to`: string, read-only display of the assigned user
- `date_reported`: timestamp, read-only
- `date_fixed`: timestamp, read-only
- `comments`: nested comment list, read-only
- `new_comment`: write-only helper field used only during update requests
- `target_defect_id`: write-only helper field used only when marking a defect as duplicate

### Comment

The comment model is exposed through nested defect responses only.

- `id`: integer
- `author`: string display of the user
- `text`: string
- `created_at`: timestamp

Comments are create-only from the defect update flow; there is no separate comment endpoint.

### DefectHistory

This model is not exposed as a public endpoint, but it powers the developer metrics feature.

- `defect`: defect reference
- `old_status`: previous status
- `new_status`: new status
- `changed_by`: user who performed the change
- `changed_at`: timestamp
- `assigned_to`: user reference recorded at the time of the change

## Authentication and Role Rules

### Session authentication

All endpoints require a logged-in Django session. The standard login page is available at `/api-auth/login/`.

### Role rules

- Testers can create defects.
- Product Owners can create products.
- Defect updates are allowed for the product owner or a product developer, but the exact status transition is still checked against the state machine.
- Product Owner-only operations include creating products and marking a defect as duplicate.
- Developers can change defect status only along the developer transitions defined in the state machine.

## Status Workflow

The allowed transitions are defined in the state machine and enforced by the defect update handler.

### Product Owner transitions

- `new` -> `open`
- `new` -> `rejected`
- `new` -> `duplicate`
- `fixed` -> `reopened`
- `fixed` -> `resolved`

### Developer transitions

- `open` -> `assigned`
- `reopened` -> `assigned`
- `assigned` -> `fixed`
- `assigned` -> `cannot_reproduce`

### Side effects during status updates

- Setting a defect to `fixed` writes `date_fixed`.
- Setting a defect to `reopened` clears `date_fixed` and `assigned_to`.
- Setting a defect to `assigned` auto-populates `assigned_to` with the authenticated developer user.
- Each status change creates a `DefectHistory` record.

## Duplicate Chain Behavior

The current implementation uses a self-referential `duplicate_of` foreign key instead of merging tester emails into the target defect.

### What happens when a defect is marked duplicate

1. Only a Product Owner can do it.
2. The source defect must currently have status `new`.
3. `target_defect_id` must be supplied.
4. The target defect must exist and belong to the same product.
5. Self-duplication is rejected.
6. Cycles are rejected.
7. The source defect is updated to `status = duplicate` and linked to the target defect through `duplicate_of`.

### Notification behavior

When a defect status changes, the signal handler walks the current duplicate tree, gathers all tester emails from the connected chain, deduplicates them, and sends one notification message to the full set.

This means:

- emails are preserved on each defect,
- the notification list is built dynamically from the chain,
- duplicate chain recipients are not stored as a merged string on the target defect.

## Endpoint Reference

### GET /api/defects/

Returns defects visible to the current user.

Visibility rules:

- Product Owners see defects for products they own.
- Developers see defects for products where they are assigned as developers.
- Other authenticated users see defects they reported, matched by `tester_email` or `tester_id`.

Query support:

- Filtering: `status`, `priority`, `tester_id`, `severity`, `assigned_to`, `title`
- Search: `title`, `description`
- Pagination: page-number pagination with page size 10

Success response shape:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "product": 1,
      "title": "Example defect",
      "description": "...",
      "steps_to_reproduce": "...",
      "tester_id": "3",
      "tester_email": "tester@example.com",
      "duplicate_of": null,
      "severity": "major",
      "priority": "high",
      "status": "new",
      "assigned_to": null,
      "date_reported": "2026-04-27T10:00:00Z",
      "date_fixed": null,
      "comments": []
    }
  ]
}
```

### POST /api/defects/

Creates a new defect report.

Role restriction: Tester only.

Required input:

- `product`
- `title`
- `description`

Optional input:

- `steps_to_reproduce`
- `tester_email`
- `severity`
- `priority`

Implemented behavior:

- `tester_id` is set from the current authenticated user.
- `tester_email` is set from the current authenticated user email.
- `status` is always set to `new`.

Example request:

```http
POST /api/defects/
Content-Type: application/json

{
  "product": 1,
  "title": "Login button not responsive",
  "description": "The button does not submit the form",
  "steps_to_reproduce": "1. Open login page\n2. Click login",
  "severity": "major",
  "priority": "high"
}
```

Success response: `201 Created` with the full defect representation.

Common errors:

- `401 Unauthorized` if the session is missing
- `403 Forbidden` if the user is not a Tester
- `400 Bad Request` for serializer validation errors

### GET /api/defects/{id}/

Returns one defect with nested comments.

Access is limited by the queryset visibility rules, so the object is only retrievable if it is visible to the current user.

Success response: `200 OK` with the same structure shown in the defect list results.

### PUT /api/defects/{id}/ and PATCH /api/defects/{id}/

Updates a defect.

Supported update behaviors:

- field edits such as `title`, `description`, `steps_to_reproduce`, `severity`, `priority`
- status changes governed by the state machine
- duplicate marking when `status = duplicate` and `target_defect_id` is supplied
- adding a comment via `new_comment`

Important restrictions:

- Only the product owner or a product developer can update a defect object.
- If a status change is requested, the transition must be valid for the user’s role.
- If `status = duplicate`, only the product owner may proceed.
- If `new_comment` is supplied, only the product owner or developer may add it.

Example status update request:

```http
PATCH /api/defects/1/
Content-Type: application/json

{
  "status": "open"
}
```

Example duplicate request:

```http
PATCH /api/defects/1/
Content-Type: application/json

{
  "status": "duplicate",
  "target_defect_id": 2
}
```

Example comment request:

```http
PATCH /api/defects/1/
Content-Type: application/json

{
  "new_comment": "Investigating this now"
}
```

Success response: `200 OK` with the updated defect representation.

### DELETE /api/defects/{id}/

Deletes a defect.

Success response: `204 No Content`.

### GET /api/defects/{id}/candidate-targets/

Returns valid duplicate targets for the current defect.

The current implementation returns defects from the same product whose status is not `new`.

Example response:

```json
[
  {"id": 2, "title": "Existing bug"},
  {"id": 3, "title": "Related defect"}
]
```

### GET /api/defects/{id}/allowed-statuses/

Returns the allowed next statuses for the current user on this defect.

Response format:

```json
{
  "allowed_statuses": [
    {"value": "open", "label": "Open"},
    {"value": "rejected", "label": "Rejected"}
  ]
}
```

If the current user is neither the product owner nor a product developer, the response is:

```json
{
  "allowed_statuses": []
}
```

### GET /api/defects/metrics/{user_id}/

Returns a developer rating based on the defect history table.

Rules:

- The user must exist.
- The user must be in the Developer group.
- The user must have at least 20 history entries where the tracked assignment field matches the developer and the status is `fixed`.
- The rating is derived from the ratio of reopened to fixed history rows.

Response examples:

```json
{
  "developer_id": 5,
  "rating": "Good"
}
```

Possible ratings:

- `Insufficient data`
- `Good`
- `Fair`
- `Poor`

Common errors:

- `404 Not Found` if the user does not exist
- `400 Bad Request` if the user exists but is not a developer

### GET /api/products/

Returns products owned by the current Product Owner.

Non-owners receive an empty result set.

Pagination applies here as well.

### POST /api/products/

Creates a product.

Role restriction: Product Owner only.

Required input:

- `product_id`
- `version`

Optional input:

- `description`
- `developers`
- `expiry_date`

Implemented behavior:

- `owner` is set from the authenticated user.
- Developers must belong to the Developer group.
- Each developer can be assigned to only one product.

Example request:

```http
POST /api/products/
Content-Type: application/json

{
  "product_id": "PROD-2048",
  "version": "1.0.0",
  "description": "Customer portal",
  "developers": [4, 5],
  "expiry_date": "2026-12-31"
}
```

Success response: `201 Created` with the full product representation.

### GET /api/products/{id}/

Returns one product owned by the current Product Owner.

If the user does not own the product, the object is not returned by the queryset.

### PUT /api/products/{id}/ and PATCH /api/products/{id}/

Updates a product owned by the current Product Owner.

Updateable fields:

- `product_id`
- `version`
- `description`
- `developers`
- `expiry_date`

Developer assignment validation is enforced again on update, including the one-product-per-developer rule.

### DELETE /api/products/{id}/

Deletes a product.

The product model uses cascading deletes, so related defects are removed as well.

## Error Reference

The following errors are explicitly implemented in the API:

| Status | When it happens |
|---|---|
| `401 Unauthorized` | The user is not logged in through a Django session |
| `403 Forbidden` | The user lacks the role needed for create/update actions |
| `400 Bad Request` | A transition is invalid, duplicate rules are violated, or serializer validation fails |
| `404 Not Found` | A referenced defect or user does not exist |
| `204 No Content` | Successful delete |

Examples of explicit error messages include:

- Only testers can submit defect reports.
- Only product owners can register products.
- Only product owner can mark a defect as duplicate.
- Target defect must belong to the same product.
- A defect cannot be marked as a duplicate of itself.
- Cannot mark a defect as a duplicate of one of its descendants.
- Transition from X to Y is not allowed for role.

## Testing Evidence

The repository already contains automated tests that cover the API behavior documented here.

Recommended validation commands:

- `python manage.py test defects.test_api`
- `python manage.py test defects.test_dev_metrics`

What these tests cover:

- defect creation, listing, retrieval, update, delete
- duplicate marking and duplicate-chain notification behavior
- comment creation through defect update
- product creation, listing, retrieval, update, delete
- filtering behavior
- developer metrics thresholds and boundary cases

## Known Limitations and Notes

- The README still describes duplicate email merging, but the implemented code now preserves emails per defect and resolves recipient lists dynamically from the duplicate chain.
- Comment editing and comment deletion are not supported.
- The email notification code is present, but the project notes indicate real SMTP delivery has not been fully debugged.
- The display label for `cannot_reproduce` is spelled `Canot_Reproduce` in the model choices; the API value remains `cannot_reproduce`.
- `product_id` is the user-facing product name, not the internal numeric database ID.

## Example Workflows

### Tester creates a defect

1. Log in as a user in the Tester group.
2. POST to `/api/defects/` with a product ID and defect details.
3. The API returns a new defect with status `new`.

### Product Owner marks a defect as duplicate

1. Log in as a Product Owner.
2. Confirm the defect is still `new`.
3. GET `/api/defects/{id}/candidate-targets/` if you want valid targets.
4. PATCH the defect with `status = duplicate` and `target_defect_id`.
5. The defect becomes linked through `duplicate_of`.

### Developer progresses a defect

1. Log in as a Developer assigned to the product.
2. GET `/api/defects/{id}/allowed-statuses/` to see valid next states.
3. PATCH the defect to `assigned`, `fixed`, or `cannot_reproduce` where allowed.
4. The API records the history entry and updates assignment/date fields as required.

## Implementation Source Map

- Routing: `core/urls.py`
- Defect and product endpoints: `defects/views.py`
- Request/response schemas: `defects/serializers.py`
- Domain model and notification behavior: `defects/models.py`
- Transition rules: `defects/state_machine.py`
- Permission helpers: `defects/permissions.py`
- Behavior tests: `defects/test_api.py`, `defects/test_dev_metrics.py`
- Duplicate-chain rationale: `docs/duplicate_chain_implementation.md`
