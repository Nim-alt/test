# Duplicate Chain Cascade Notifications

This document explains how duplicate defects are represented and how status notifications now cascade through the full duplicate chain.

## What Was Implemented

The defect duplicate flow was changed from email merging to an explicit parent-child relationship:

- Each defect can point to a parent defect using `duplicate_of`.
- The original tester email on each defect is preserved.
- Notifications are sent to every tester email found in the connected duplicate chain.
- Duplicate re-parenting is validated so a defect cannot point to itself or one of its descendants.

## Files Changed

### `defects/models.py`

- Added `duplicate_of` as a self-referential foreign key on `Defect`.
- Added helper functions to:
  - split comma-separated tester emails,
  - find the root defect of a duplicate chain,
  - collect the full chain of related defects,
  - collect unique notification recipients from that chain.
- Updated the post-save notification signal so a status change sends one email to all testers in the connected chain.

### `defects/views.py`

- Updated the duplicate-marking branch in `DefectViewSet.update()`.
- Removed the old email-merging behavior.
- Added validation for:
  - self-duplication,
  - cyclic duplicate chains,
  - same-product restrictions.
- The source defect is now marked `duplicate` and linked to the target defect using `duplicate_of`.

### `defects/serializers.py`

- Exposed `duplicate_of` in `DefectSerializer` so the relationship is visible in API responses.

### `defects/migrations/0005_defect_duplicate_of.py`

- Added the database migration for the new `duplicate_of` field.

### `defects/test_api.py`

- Added tests verifying that duplicate marking does not merge tester emails.
- Added tests verifying that status changes notify the full duplicate chain.
- Added tests covering both parent-to-child and child-to-parent notification triggers.

### `core/settings.py`

- Enabled DRF page-number pagination so list endpoints return a consistent response shape.

## How It Works

### 1. Marking a defect as duplicate

When a product owner marks a defect as duplicate:

1. The target defect is looked up.
2. The code checks that the target belongs to the same product.
3. The code rejects invalid links:
   - a defect cannot be a duplicate of itself,
   - a defect cannot be linked to one of its descendants.
4. The source defect is updated:
   - `status = 'duplicate'`
   - `duplicate_of = target_defect`
5. No tester emails are merged.

### 2. Sending notifications

When a defect changes status:

1. The previous status is captured in `pre_save`.
2. After save, the notification handler checks whether the status changed.
3. The handler resolves the connected duplicate chain:
   - find the root defect,
   - walk through all descendant duplicates recursively,
   - collect tester emails from every defect in the chain.
4. A single notification is sent to the deduplicated recipient list.

### 3. Re-parenting behavior

If a defect is later linked to a different duplicate parent, future notifications follow the new chain only. The chain is always resolved from the current `duplicate_of` relationships at send time.

## Validation

The defects API test suite was run successfully after the implementation:

```powershell
python manage.py test defects.test_api
```

## Notes

- Existing tester emails remain stored on each defect.
- The notification chain uses the current parent-child graph, not merged email history.
- Pagination warnings were removed by adding stable ordering to the queryset methods.