# PostgreSQL Backup and Restore — Operations Runbook

## Overview

CTEDemo uses PostgreSQL (Docker container `eupraxis-db`) for production data. This runbook covers manual backup, verification, restore, and retention procedures.

All scripts are in `scripts/` and run on-demand. No automated scheduling is configured — admin runs scripts manually or sets up cron as needed.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup.sh` | Create a compressed pg_dump backup |
| `scripts/verify-backup.sh` | Verify backup integrity by restoring to temp DB |
| `scripts/restore-db.sh` | Restore production database from backup |
| `scripts/retention.py` | Clean up old backups per retention policy |

## Backup

```bash
scripts/backup.sh
```

- Creates `backups/eupraxis_backup_YYYY-MM-DD.sql.gz`
- Date-only granularity (one per day; re-running overwrites)
- Checks 500MB minimum free disk space before starting
- Requires Docker container `eupraxis-db` to be running
- Environment: `BACKUP_DIR` (default: `./backups`), `CONTAINER_NAME` (default: `eupraxis-db`)

## Verification

```bash
scripts/verify-backup.sh                  # verify latest backup
scripts/verify-backup.sh 2026-03-15       # verify specific date
```

- Restores backup to temporary `eupraxis_verify` database
- Runs integrity checks (table count, row counts)
- Logs results to `backups/verify-YYYY-MM-DD.log`
- Drops temporary database after verification
- Exit 0 on pass, non-zero on fail

## Restore

```bash
scripts/restore-db.sh 2026-03-15
```

**WARNING: This is a destructive operation.** The script:

1. Validates date format and finds backup file
2. Shows confirmation prompt (database name, backup date, file size)
3. Stops backend service (`docker compose stop backend`)
4. Drops and recreates the database
5. Restores from compressed backup
6. Checks Alembic migration state (`alembic current`)
7. Starts backend service (`docker compose start backend`)

After restore, verify the application: `curl http://localhost:8000/api/v1/health`

## Retention

```bash
scripts/retention.py --dry-run            # preview what would be deleted
scripts/retention.py                       # actually delete expired backups
scripts/retention.py --backup-dir /path    # custom backup directory
```

**Retention tiers:**

| Tier | Rule | Period |
|------|------|--------|
| Daily | Keep all backups | Last 7 days |
| Weekly | Keep Sunday backups | Last 4 weeks |
| Monthly | Keep 1st-of-month backups | Last 12 months |

Backups older than 12 months and not matching any tier are deleted. Always run `--dry-run` first.

## Off-Server Copy

Backups are local by default. To copy off-server, use rsync after backup:

```bash
rsync -avz ./backups/eupraxis_backup_YYYY-MM-DD.sql.gz user@remote:/backups/
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Database container not running" | `docker compose up -d db` |
| "Insufficient disk space" | Free up space or set `MIN_SPACE_MB` lower |
| "No backup found for date" | Run `scripts/retention.py --dry-run` to see available backups |
| Restore fails mid-way | Database may be in partial state — re-run restore or restore from another date |
| "No alembic_version table" | Run `cd backend && alembic upgrade head` after restore |

## File Locations

- Backups: `./backups/eupraxis_backup_YYYY-MM-DD.sql.gz`
- Verification logs: `./backups/verify-YYYY-MM-DD.log`
- Helper utilities: `scripts/backup_helpers.py`
- Retention logic: `scripts/retention.py`
