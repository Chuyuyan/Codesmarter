# Database Migration Fix

## ✅ Issue Fixed

The error `sqlite3.OperationalError: no such column: users.phone_number` occurred because:
1. The `phone_number` field was added to the User model
2. The existing database didn't have this column yet

## 🔧 Solution Applied

I've created a migration script that:
- ✅ Adds the `phone_number` column to the `users` table
- ✅ Creates an index on the column
- ✅ Is safe to run multiple times (checks if column exists first)
- ✅ Runs automatically when the server starts

## 📝 Migration Status

The migration has been run and the column now exists in your database.

## 🔄 Next Step: Restart Your Server

**You need to restart your Flask server** for the changes to take effect:

1. Stop your current server (Ctrl+C)
2. Start it again:
   ```bash
   python -m backend.app
   ```

The server will automatically run the migration on startup if needed.

## ✅ Verification

After restarting, try the password reset again. It should work now!

If you still see errors, check:
- Server logs for migration messages
- Database file location: `data/users.db`
- That the server restarted properly

## 🛠️ Manual Migration (If Needed)

If you ever need to run the migration manually:

```bash
python migrate_database.py
```

This script is safe to run multiple times - it checks if the column exists before adding it.

