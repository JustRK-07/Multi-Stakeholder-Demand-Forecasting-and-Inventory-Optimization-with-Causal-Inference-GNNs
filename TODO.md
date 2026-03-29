# Remaining Work

## Platform
- Move file-backed users, sessions, settings, datasets, and audit logs to a database-backed persistence layer.
- Expand role-based authorization beyond the current admin/analyst controls.

## API / Jobs
- Add a background job runner for long-running uploads, retraining, and scheduled drift scans.
- Decide whether to harden all analytics endpoints behind backend auth checks or keep them open for demo mode.

## ML / MLOps
- Promote local artifacts into a versioned model registry.
- Add scheduled retraining and benchmark reporting per dataset version.
- Replace the current federated approximation with a true cross-client training workflow if federated learning remains in scope.

## Frontend
- Add deeper end-to-end UI tests around dataset history, monitoring, and multi-user role behavior.
