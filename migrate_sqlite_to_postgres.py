#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for market-pie5-bot

Migrates data from:
- bot_auth.db (authentication data)
- logs/trading_logs.db (trading logs - 76MB with ~59,917 trades)

To PostgreSQL database configured in DATABASE_URL environment variable.

Usage:
    # Set PostgreSQL connection
    export DATABASE_URL="postgresql://marketbot_user@localhost:5435/marketbot"
    
    # Run migration
    python migrate_sqlite_to_postgres.py
    
    # Dry run (no changes)
    python migrate_sqlite_to_postgres.py --dry-run
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database import Base, SessionLocal, engine, is_postgres


def check_prerequisites():
    """Check if prerequisites are met before migration"""
    print("🔍 Checking prerequisites...")
    
    # Check if PostgreSQL is configured
    if not is_postgres:
        print("❌ DATABASE_URL is not configured for PostgreSQL")
        print("   Set environment variable: export DATABASE_URL='postgresql://user@host:port/db'")
        return False
    
    print("✅ PostgreSQL connection configured")
    
    # Test PostgreSQL connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False
    
    # Check if SQLite databases exist
    sqlite_dbs = {
        'auth': Path('bot_auth.db'),
        'trading': Path('logs/trading_logs.db'),
        'fallback': Path('bot.db')
    }
    
    found_dbs = {}
    for name, path in sqlite_dbs.items():
        if path.exists():
            size = path.stat().st_size
            print(f"✅ Found {name} database: {path} ({size:,} bytes)")
            found_dbs[name] = path
        else:
            print(f"⚠️  Not found: {path}")
    
    if not found_dbs:
        print("❌ No SQLite databases found to migrate")
        return False
    
    return found_dbs


def backup_sqlite_databases(databases: Dict[str, Path]):
    """Create backups of SQLite databases before migration"""
    print("\n📦 Creating backups...")
    backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    for name, db_path in databases.items():
        backup_path = backup_dir / f"{name}_{db_path.name}"
        
        # Use SQLite backup API for consistent backup
        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(backup_path))
        
        with dest:
            source.backup(dest)
        
        source.close()
        dest.close()
        
        print(f"✅ Backed up {name}: {backup_path}")
    
    print(f"\n✅ Backups saved to: {backup_dir}")
    return backup_dir


def migrate_auth_tables(sqlite_path: Path, pg_session: Session, dry_run: bool = False):
    """Migrate authentication tables from bot_auth.db or bot.db"""
    print("\n🔄 Migrating authentication data...")
    
    # Connect to SQLite
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("⚠️  No authentication tables found")
        conn.close()
        return
    
    print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
    
    total_rows = 0
    
    for table in tables:
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"  ⏭️  Skipping empty table: {table}")
            continue
        
        print(f"  📊 Migrating {table}: {count:,} rows")
        
        if dry_run:
            print(f"     [DRY RUN] Would migrate {count} rows from {table}")
            total_rows += count
            continue
        
        # Fetch all rows
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Build INSERT query for PostgreSQL (auth schema)
        placeholders = ', '.join([f":{col}" for col in columns])
        insert_sql = f"INSERT INTO auth.{table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            for row in batch:
                try:
                    pg_session.execute(text(insert_sql), dict(row))
                except Exception as e:
                    print(f"     ⚠️  Error migrating row: {e}")
            
            pg_session.commit()
            print(f"     ✅ Migrated {min(i+batch_size, len(rows))}/{len(rows)} rows")
        
        total_rows += count
    
    conn.close()
    print(f"✅ Auth migration complete: {total_rows:,} total rows")


def migrate_trading_logs(sqlite_path: Path, pg_session: Session, dry_run: bool = False):
    """Migrate trading logs from logs/trading_logs.db"""
    print("\n🔄 Migrating trading logs (this may take a while for large databases)...")
    
    # Column name mapping (SQLite -> PostgreSQL)
    # metadata columns were renamed to avoid SQLAlchemy reserved word conflict
    column_mapping = {
        'trades': {'metadata': 'trade_metadata'},
        'system_logs': {'metadata': 'log_metadata'},
        'backtest_results': {'metadata': 'backtest_metadata'},
        'performance_metrics': {'metadata': 'metric_metadata'}
    }
    
    # Connect to SQLite
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Tables to migrate
    tables = ['trades', 'system_logs', 'backtest_results', 'performance_metrics']
    
    total_rows = 0
    
    for table in tables:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cursor.fetchone():
            print(f"  ⏭️  Table not found: {table}")
            continue
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"  ⏭️  Skipping empty table: {table}")
            continue
        
        print(f"  📊 Migrating {table}: {count:,} rows")
        
        if dry_run:
            print(f"     [DRY RUN] Would migrate {count} rows from {table}")
            total_rows += count
            continue
        
        # For large tables, use cursor to avoid loading all data into memory
        batch_size = 5000
        offset = 0
        migrated = 0
        
        while True:
            # Fetch batch
            cursor.execute(f"SELECT * FROM {table} LIMIT {batch_size} OFFSET {offset}")
            rows = cursor.fetchall()
            
            if not rows:
                break
            
            # Get column names (only once)
            if offset == 0:
                sqlite_columns = [desc[0] for desc in cursor.description]
                # Apply column name mapping for PostgreSQL
                pg_columns = [column_mapping[table].get(col, col) if table in column_mapping else col for col in sqlite_columns]
                placeholders = ', '.join([f":{col}" for col in pg_columns])
                insert_sql = f"INSERT INTO trading.{table} ({', '.join(pg_columns)}) VALUES ({placeholders})"
            
            # Insert batch
            for row in rows:
                try:
                    # Map column names in row dict
                    row_dict = dict(row)
                    if table in column_mapping:
                        for old_name, new_name in column_mapping[table].items():
                            if old_name in row_dict:
                                row_dict[new_name] = row_dict.pop(old_name)
                    pg_session.execute(text(insert_sql), row_dict)
                except Exception as e:
                    print(f"     ⚠️  Error migrating row: {e}")
            
            pg_session.commit()
            migrated += len(rows)
            print(f"     ✅ Migrated {migrated:,}/{count:,} rows ({migrated*100//count}%)")
            
            offset += batch_size
        
        total_rows += count
    
    conn.close()
    print(f"✅ Trading logs migration complete: {total_rows:,} total rows")


def verify_migration(databases: Dict[str, Path]):
    """Verify migration by comparing row counts"""
    print("\n🔍 Verifying migration...")
    
    pg_session = SessionLocal()
    
    # Verify auth tables
    if 'auth' in databases or 'fallback' in databases:
        sqlite_path = databases.get('auth', databases.get('fallback'))
        conn = sqlite3.connect(str(sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n📊 Authentication tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor.fetchone()[0]
            
            try:
                result = pg_session.execute(text(f"SELECT COUNT(*) FROM auth.{table}"))
                pg_count = result.scalar()
                
                if sqlite_count == pg_count:
                    print(f"  ✅ {table}: {sqlite_count:,} rows (match)")
                else:
                    print(f"  ⚠️  {table}: SQLite={sqlite_count:,}, PostgreSQL={pg_count:,} (MISMATCH)")
            except Exception as e:
                print(f"  ❌ {table}: Error verifying - {e}")
        
        conn.close()
    
    # Verify trading logs
    if 'trading' in databases:
        conn = sqlite3.connect(str(databases['trading']))
        cursor = conn.cursor()
        
        tables = ['trades', 'system_logs', 'backtest_results', 'performance_metrics']
        
        print("\n📊 Trading log tables:")
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                continue
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor.fetchone()[0]
            
            try:
                result = pg_session.execute(text(f"SELECT COUNT(*) FROM trading.{table}"))
                pg_count = result.scalar()
                
                if sqlite_count == pg_count:
                    print(f"  ✅ {table}: {sqlite_count:,} rows (match)")
                else:
                    print(f"  ⚠️  {table}: SQLite={sqlite_count:,}, PostgreSQL={pg_count:,} (MISMATCH)")
            except Exception as e:
                print(f"  ❌ {table}: Error verifying - {e}")
        
        conn.close()
    
    pg_session.close()
    print("\n✅ Verification complete")


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--skip-backup', action='store_true', help='Skip backup creation (not recommended)')
    parser.add_argument('--skip-verify', action='store_true', help='Skip post-migration verification')
    args = parser.parse_args()
    
    print("=" * 80)
    print("SQLite to PostgreSQL Migration Script")
    print("market-pie5-bot Database Migration")
    print("=" * 80)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Check prerequisites
    databases = check_prerequisites()
    if not databases:
        sys.exit(1)
    
    # Create backups
    if not args.skip_backup and not args.dry_run:
        backup_dir = backup_sqlite_databases(databases)
    
    # Create database schema
    if not args.dry_run:
        print("\n🏗️  Creating database schema...")
        Base.metadata.create_all(bind=engine)
        print("✅ Schema created")
    
    # Get PostgreSQL session
    pg_session = SessionLocal()
    
    try:
        # Migrate authentication data
        if 'auth' in databases:
            migrate_auth_tables(databases['auth'], pg_session, dry_run=args.dry_run)
        elif 'fallback' in databases:
            migrate_auth_tables(databases['fallback'], pg_session, dry_run=args.dry_run)
        
        # Migrate trading logs
        if 'trading' in databases:
            migrate_trading_logs(databases['trading'], pg_session, dry_run=args.dry_run)
        
        print("\n" + "=" * 80)
        print("✅ Migration complete!")
        print("=" * 80)
        
        # Verify migration
        if not args.skip_verify and not args.dry_run:
            verify_migration(databases)
        
        # Final instructions
        if not args.dry_run:
            print("\n📋 Next steps:")
            print("   1. Verify data integrity by checking a few records")
            print("   2. Update docker-compose.yml to use PostgreSQL")
            print("   3. Restart the application")
            print(f"   4. If everything works, you can archive SQLite files")
            if not args.skip_backup:
                print(f"   5. Backups are saved in: {backup_dir}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        pg_session.close()


if __name__ == "__main__":
    main()
