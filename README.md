# AutoUpdate - Automated GitHub Activity

This repository uses GitHub Actions to automate daily activity updates.

## Workflow Details
- Runs automatically via scheduled cron (`0 0 * * *` - 00:00 UTC daily).
- Supports manual triggers via `workflow_dispatch`.
- Updates `activity_log.txt` and commits back to the main branch.
