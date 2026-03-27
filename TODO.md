# Remaining Work

## Platform
- Add role-based authorization instead of route-level session gating only.
- Move file-backed users, sessions, settings, and dataset registry to a database.
- Add audit logging for login, password change, dataset activation, and dataset deletion.

## API
- Add route-level FastAPI tests for auth, dataset lifecycle, and analytics endpoints.
- Add pagination and archive semantics for dataset history.
- Add background jobs for model retraining, drift scans, and long-running uploads.

## ML / MLOps
- Promote local artifacts into a versioned model registry.
- Add scheduled retraining and benchmark reporting per dataset version.
- Add historical drift tracking and alert delivery instead of point-in-time monitoring only.
- Replace the current federated approximation with a true cross-client training workflow if federated learning remains in scope.

## Frontend
- Add dedicated dataset history and monitoring pages instead of dashboard-only summaries.
- Add richer frontend integration tests for auth, upload, settings, and dashboard flows.
- Add user profile editing and session-expiry handling.
