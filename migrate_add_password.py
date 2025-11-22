#!/usr/bin/env python3
"""
Database Migration: Add password_hash column to users table
Run this once on production to add password support to existing users table.
"""

import os
import sys

def migrate_database():
    """Add password_hash column to users table if it doesn't exist"""
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print(" DATABASE_URL not set - using SQLite for local development")
        import sqlite3
        conn = sqlite3.connect('securecloudx.db')
        cursor = conn.cursor()
        db_type = "SQLite"
    else:
        print(" Using PostgreSQL from DATABASE_URL")
        try:
            import psycopg2
            # Fix Heroku/Render postgres:// URL
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(database_url, sslmode='require')
            cursor = conn.cursor()
            db_type = "PostgreSQL"
        except Exception as e:
            print(f" Failed to connect to PostgreSQL: {e}")
            sys.exit(1)
    
    print(f"\n Running migration on {db_type}...")
    
    try:
        # Step 1: Check if password_hash column exists
        if db_type == "PostgreSQL":
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password_hash'
            """)
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            cursor.execute("SELECT 1")  # Reset cursor
        
        has_password_hash = bool(cursor.fetchone()) if db_type == "PostgreSQL" else 'password_hash' in columns
        
        if has_password_hash:
            print(" Column 'password_hash' already exists - no migration needed")
        else:
            print(" Adding 'password_hash' column to users table...")
            
            # Step 2: Add the column with a default value
            if db_type == "PostgreSQL":
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN password_hash TEXT DEFAULT 'MIGRATION_REQUIRED'
                """)
                # Make it NOT NULL after setting default
                cursor.execute("""
                    ALTER TABLE users 
                    ALTER COLUMN password_hash SET NOT NULL
                """)
            else:
                # SQLite doesn't support ALTER COLUMN easily, need to recreate
                cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT 'MIGRATION_REQUIRED'")
            
            conn.commit()
            print(" Column 'password_hash' added successfully")
        
        # Step 3: Check for users with temporary password
        cursor.execute("SELECT id, username FROM users WHERE password_hash = 'MIGRATION_REQUIRED' OR password_hash IS NULL")
        old_users = cursor.fetchall()
        
        if old_users:
            print(f"\n  Found {len(old_users)} users without passwords:")
            for user_id, username in old_users:
                print(f"   - ID {user_id}: {username}")
            
            print("\n  Deleting old users and their data (they can re-register with passwords)...")
            for user_id, username in old_users:
                # Delete in order to respect foreign key constraints
                placeholder = '%s' if db_type == 'PostgreSQL' else '?'
                
                # 1. Delete file shares where user is recipient
                cursor.execute(f"DELETE FROM file_shares WHERE recipient_id = {placeholder}", (user_id,))
                
                # 2. Delete file shares where user is owner
                cursor.execute(f"DELETE FROM file_shares WHERE owner_id = {placeholder}", (user_id,))
                
                # 3. Delete files owned by user
                cursor.execute(f"DELETE FROM files WHERE owner_id = {placeholder}", (user_id,))
                
                # 4. Delete user sessions
                cursor.execute(f"DELETE FROM user_sessions WHERE user_id = {placeholder}", (user_id,))
                
                # 5. Finally delete the user
                cursor.execute(f"DELETE FROM users WHERE id = {placeholder}", (user_id,))
                
                print(f"   ✓ Deleted user and data: {username}")
            
            conn.commit()
            print("\n Old users and their data deleted - they need to re-register with passwords")
        else:
            print(" All users have valid passwords")
        
        # Step 4: Clear blockchain (since old data may be corrupted)
        print("\n Clearing blockchain blocks...")
        cursor.execute("DELETE FROM blockchain_blocks")
        conn.commit()
        print(" Blockchain cleared - will recreate genesis on startup")
        
        conn.close()
        print("\n Migration completed successfully!")
        print("\n Next steps:")
        print("   1. Old users deleted - they need to re-register")
        print("   2. Blockchain reset - will auto-recreate on startup")
        print("   3. Deploy updated code to production")
        
    except Exception as e:
        conn.rollback()
        print(f"\n Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print(" DATABASE MIGRATION: Add Password Authentication")
    print("=" * 60)
    migrate_database()
