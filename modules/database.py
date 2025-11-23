"""
Database Module
Handles database operations for users and files.
Supports both SQLite (local) and PostgreSQL (production).
"""

import os
import sqlite3
from typing import Optional, List, Dict
from contextlib import contextmanager


class Database:
    """
    Manages database connections and operations for SecureCloudX.
    Automatically uses PostgreSQL if DATABASE_URL is set, otherwise SQLite.
    """
    
    def __init__(self, db_path: str = 'securecloudx.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (used only if DATABASE_URL not set)
        """
        self.db_path = db_path
        self.database_url = os.getenv('DATABASE_URL')
        
        # Detect database type
        if self.database_url:
            # PostgreSQL for production (Render/Heroku)
            import psycopg2
            import psycopg2.extras
            self.is_postgres = True
            self.db_module = psycopg2
            # Fix for Heroku's postgres:// URL
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        else:
            # SQLite for local development
            self.is_postgres = False
            self.db_module = sqlite3
        
        self.init_database()
    
    def _get_placeholder(self, count=1):
        """
        Get the correct SQL parameter placeholder for the database type.
        
        Args:
            count: Number of placeholders needed
            
        Returns:
            str: Placeholder string (? for SQLite, %s for PostgreSQL)
        """
        if self.is_postgres:
            return ', '.join(['%s'] * count) if count > 1 else '%s'
        else:
            return ', '.join(['?'] * count) if count > 1 else '?'

    def _safe_execute(self, cursor, sql: str, params: tuple = None):
        """
        Execute SQL safely, swallowing duplicate-key races that can happen
        when multiple worker processes try to create the same objects at once.
        """
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
        except Exception as e:
            # If Postgres unique violation occurred due to race during
            # concurrent CREATE statements, log and ignore; otherwise re-raise.
            try:
                import psycopg2
                # psycopg2 provides pgcode on DBAPIError instances
                pgcode = getattr(e, 'pgcode', None)
                if pgcode == '23505':
                    # Unique violation - likely a concurrent creation race
                    return
            except Exception:
                pass

            # Fallback textual check for duplicate key errors
            if 'duplicate key value' in str(e).lower() or 'already exists' in str(e).lower():
                return

            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            Connection: Database connection (psycopg2 or sqlite3)
        """
        if self.is_postgres:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(self.database_url, sslmode='require')
            conn.cursor_factory = psycopg2.extras.RealDictCursor
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """
        Create database tables if they don't exist.
        Compatible with both PostgreSQL and SQLite.
        Auto-migrates old schemas by adding missing columns.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if self.is_postgres:
                # PostgreSQL syntax - use _safe_execute to avoid race conditions
                self._safe_execute(cursor, '''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ecc_public_key TEXT NOT NULL,
                        ecc_private_key TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Auto-migration: Add password_hash if it doesn't exist
                try:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='password_hash'
                    """)
                    if not cursor.fetchone():
                        print(" Auto-migration: Adding password_hash column to users table...")
                        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT 'MIGRATION_REQUIRED'")
                        cursor.execute("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL")
                        print(" Migration complete: password_hash column added")
                except Exception as e:
                    # Column might already exist or other schema issue
                    pass

                self._safe_execute(cursor, '''
                    CREATE TABLE IF NOT EXISTS files (
                        id SERIAL PRIMARY KEY,
                        owner_id INTEGER NOT NULL,
                        filename TEXT NOT NULL,
                        stored_path TEXT NOT NULL,
                        block_index INTEGER NOT NULL,
                        encrypted_data TEXT NOT NULL,
                        iv TEXT NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (owner_id) REFERENCES users (id)
                    )
                ''')

                self._safe_execute(cursor, '''
                    CREATE TABLE IF NOT EXISTS file_shares (
                        id SERIAL PRIMARY KEY,
                        file_id INTEGER NOT NULL,
                        owner_id INTEGER NOT NULL,
                        recipient_id INTEGER NOT NULL,
                        encrypted_aes_key TEXT NOT NULL,
                        block_index INTEGER NOT NULL,
                        shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (file_id) REFERENCES files (id),
                        FOREIGN KEY (owner_id) REFERENCES users (id),
                        FOREIGN KEY (recipient_id) REFERENCES users (id)
                    )
                ''')

                self._safe_execute(cursor, '''
                    CREATE TABLE IF NOT EXISTS blockchain_blocks (
                        id SERIAL PRIMARY KEY,
                        block_index INTEGER NOT NULL UNIQUE,
                        block_timestamp REAL NOT NULL,
                        block_data TEXT NOT NULL,
                        previous_hash TEXT NOT NULL,
                        block_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Session storage table for authentication
                self._safe_execute(cursor, '''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        token TEXT NOT NULL UNIQUE,
                        user_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
            else:
                # SQLite syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ecc_public_key TEXT NOT NULL,
                        ecc_private_key TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        owner_id INTEGER NOT NULL,
                        filename TEXT NOT NULL,
                        stored_path TEXT NOT NULL,
                        block_index INTEGER NOT NULL,
                        encrypted_data TEXT NOT NULL,
                        iv TEXT NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (owner_id) REFERENCES users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_shares (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER NOT NULL,
                        owner_id INTEGER NOT NULL,
                        recipient_id INTEGER NOT NULL,
                        encrypted_aes_key TEXT NOT NULL,
                        block_index INTEGER NOT NULL,
                        shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (file_id) REFERENCES files (id),
                        FOREIGN KEY (owner_id) REFERENCES users (id),
                        FOREIGN KEY (recipient_id) REFERENCES users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blockchain_blocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        block_index INTEGER NOT NULL UNIQUE,
                        block_timestamp REAL NOT NULL,
                        block_data TEXT NOT NULL,
                        previous_hash TEXT NOT NULL,
                        block_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Session storage table for authentication
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token TEXT NOT NULL UNIQUE,
                        user_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
    
    # User operations
    
    def create_user(self, username: str, password_hash: str, public_key: str, private_key: str) -> int:
        """
        Create a new user in the database.
        
        Args:
            username: Unique username
            password_hash: Bcrypt hashed password
            public_key: ECC public key in PEM format
            private_key: ECC private key in PEM format
            
        Returns:
            int: User ID of newly created user
            
        Raises:
            sqlite3.IntegrityError: If username already exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = self._get_placeholder(4)
            cursor.execute(
                f'INSERT INTO users (username, password_hash, ecc_public_key, ecc_private_key) VALUES ({placeholders})',
                (username, password_hash, public_key, private_key)
            )
            if self.is_postgres:
                cursor.execute('SELECT lastval()')
                result = cursor.fetchone()
                return result['lastval'] if isinstance(result, dict) else result[0]
            return cursor.lastrowid
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            dict or None: User data if found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(f'SELECT * FROM users WHERE id = {placeholder}', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            dict or None: User data if found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(f'SELECT * FROM users WHERE username = {placeholder}', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all users (for listing/sharing purposes).
        
        Returns:
            List[dict]: List of all users
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, created_at FROM users')
            return [dict(row) for row in cursor.fetchall()]
    
    # File operations
    
    def create_file(self, owner_id: int, filename: str, stored_path: str, 
                    block_index: int, encrypted_data: str, iv: str) -> int:
        """
        Create a new file record in the database.
        
        Args:
            owner_id: ID of file owner
            filename: Original filename
            stored_path: Path where encrypted file is stored
            block_index: Index of blockchain block containing the AES key
            encrypted_data: Base64 encoded encrypted file data
            iv: Base64 encoded initialization vector
            
        Returns:
            int: File ID of newly created record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = self._get_placeholder(6)
            cursor.execute(
                f'''INSERT INTO files 
                   (owner_id, filename, stored_path, block_index, encrypted_data, iv) 
                   VALUES ({placeholders})''',
                (owner_id, filename, stored_path, block_index, encrypted_data, iv)
            )
            if self.is_postgres:
                cursor.execute('SELECT lastval()')
                result = cursor.fetchone()
                return result['lastval'] if isinstance(result, dict) else result[0]
            return cursor.lastrowid
    
    def get_file_by_id(self, file_id: int) -> Optional[Dict]:
        """
        Retrieve file record by ID.
        
        Args:
            file_id: File ID
            
        Returns:
            dict or None: File data if found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(f'SELECT * FROM files WHERE id = {placeholder}', (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_files_by_owner(self, owner_id: int) -> List[Dict]:
        """
        Get all files owned by a specific user.
        
        Args:
            owner_id: Owner's user ID
            
        Returns:
            List[dict]: List of file records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(f'SELECT * FROM files WHERE owner_id = {placeholder}', (owner_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_file(self, file_id: int) -> bool:
        """
        Delete a file record.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            bool: True if file was deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(f'DELETE FROM files WHERE id = {placeholder}', (file_id,))
            return cursor.rowcount > 0
    
    # File sharing operations
    
    def create_file_share(self, file_id: int, owner_id: int, recipient_id: int, 
                         encrypted_aes_key: str, block_index: int) -> int:
        """
        Create a file share record.
        
        Args:
            file_id: ID of file being shared
            owner_id: ID of file owner
            recipient_id: ID of recipient user
            encrypted_aes_key: AES key encrypted with recipient's public key
            block_index: Blockchain block index for this share
            
        Returns:
            int: Share record ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = self._get_placeholder(5)
            cursor.execute(
                f'''INSERT INTO file_shares 
                   (file_id, owner_id, recipient_id, encrypted_aes_key, block_index) 
                   VALUES ({placeholders})''',
                (file_id, owner_id, recipient_id, encrypted_aes_key, block_index)
            )
            if self.is_postgres:
                cursor.execute('SELECT lastval()')
                result = cursor.fetchone()
                return result['lastval'] if isinstance(result, dict) else result[0]
            return cursor.lastrowid
    
    def get_shared_files_for_user(self, recipient_id: int) -> List[Dict]:
        """
        Get all files shared with a specific user.
        
        Args:
            recipient_id: Recipient's user ID
            
        Returns:
            List[dict]: List of shared file records with file details
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(
                f'''SELECT fs.*, f.filename, f.encrypted_data, f.iv, u.username as owner_username
                   FROM file_shares fs
                   JOIN files f ON fs.file_id = f.id
                   JOIN users u ON fs.owner_id = u.id
                   WHERE fs.recipient_id = {placeholder}''',
                (recipient_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_file_share(self, file_id: int, recipient_id: int) -> Optional[Dict]:
        """
        Get a specific file share record.
        
        Args:
            file_id: File ID
            recipient_id: Recipient user ID
            
        Returns:
            dict or None: Share record if found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph1, ph2 = (self._get_placeholder(), self._get_placeholder())
            cursor.execute(
                f'SELECT * FROM file_shares WHERE file_id = {ph1} AND recipient_id = {ph2}',
                (file_id, recipient_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Blockchain persistence operations
    
    def save_blockchain_block(self, block_index: int, timestamp: float, data: dict, 
                              previous_hash: str, block_hash: str) -> int:
        """
        Save a blockchain block to the database using UPSERT to avoid duplicates.
        
        Args:
            block_index: Block index in the chain
            timestamp: Block timestamp
            data: Block data as dictionary
            previous_hash: Previous block hash
            block_hash: Current block hash
            
        Returns:
            int: Database ID of saved block
        """
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.is_postgres:
                # PostgreSQL UPSERT - update if exists, insert if not
                cursor.execute(
                    '''INSERT INTO blockchain_blocks 
                       (block_index, block_timestamp, block_data, previous_hash, block_hash) 
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (block_index) 
                       DO UPDATE SET 
                           block_timestamp = EXCLUDED.block_timestamp,
                           block_data = EXCLUDED.block_data,
                           previous_hash = EXCLUDED.previous_hash,
                           block_hash = EXCLUDED.block_hash
                       RETURNING id''',
                    (block_index, timestamp, json.dumps(data), previous_hash, block_hash)
                )
                result = cursor.fetchone()
                return result['id'] if isinstance(result, dict) else result[0]
            else:
                # SQLite UPSERT
                cursor.execute(
                    '''INSERT INTO blockchain_blocks 
                       (block_index, block_timestamp, block_data, previous_hash, block_hash) 
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(block_index) 
                       DO UPDATE SET 
                           block_timestamp = excluded.block_timestamp,
                           block_data = excluded.block_data,
                           previous_hash = excluded.previous_hash,
                           block_hash = excluded.block_hash''',
                    (block_index, timestamp, json.dumps(data), previous_hash, block_hash)
                )
                return cursor.lastrowid
    
    def load_blockchain_blocks(self) -> List[Dict]:
        """
        Load all blockchain blocks from the database, ordered by block_index.
        
        Returns:
            List[dict]: List of blockchain blocks
        """
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM blockchain_blocks ORDER BY block_index ASC'
            )
            blocks = []
            for row in cursor.fetchall():
                block_dict = dict(row)
                # Parse the JSON data string back to dict
                block_dict['block_data'] = json.loads(block_dict['block_data'])
                blocks.append(block_dict)
            return blocks
    
    def clear_blockchain_blocks(self):
        """
        Clear all blockchain blocks from the database.
        Useful for testing or resetting the blockchain.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM blockchain_blocks')
    
    # Session management operations
    
    def create_session(self, token: str, user_id: int, expires_at: str) -> int:
        """
        Create a new user session.
        
        Args:
            token: Session token
            user_id: User ID
            expires_at: Expiration timestamp (ISO format string)
            
        Returns:
            int: Session ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = self._get_placeholder(3)
            cursor.execute(
                f'INSERT INTO user_sessions (token, user_id, expires_at) VALUES ({placeholders})',
                (token, user_id, expires_at)
            )
            if self.is_postgres:
                cursor.execute('SELECT lastval()')
                result = cursor.fetchone()
                return result['lastval'] if isinstance(result, dict) else result[0]
            return cursor.lastrowid
    
    def get_session(self, token: str) -> Optional[Dict]:
        """
        Retrieve session by token.
        
        Args:
            token: Session token
            
        Returns:
            dict or None: Session data if found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(
                f'SELECT * FROM user_sessions WHERE token = {placeholder}',
                (token,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_session(self, token: str):
        """
        Delete a session by token.
        
        Args:
            token: Session token to delete
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self._get_placeholder()
            cursor.execute(
                f'DELETE FROM user_sessions WHERE token = {placeholder}',
                (token,)
            )
    
    def cleanup_expired_sessions(self):
        """
        Delete all expired sessions from database.
        Should be called periodically.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP'
            )
    
    def acquire_blockchain_lock(self, timeout: int = 10) -> bool:
        """
        Acquire a PostgreSQL advisory lock for blockchain initialization.
        This prevents multiple workers from racing during blockchain setup.
        
        Args:
            timeout: Maximum seconds to wait for lock
            
        Returns:
            bool: True if lock acquired, False otherwise
        """
        if not self.is_postgres:
            # SQLite doesn't need advisory locks (single process)
            return True
        
        try:
            import psycopg2
            import logging
            logger = logging.getLogger(__name__)
            
            # Use a fixed lock ID for blockchain initialization
            lock_id = 123456789
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Try to acquire lock with timeout
                cursor.execute("SELECT pg_try_advisory_lock(%s)", (lock_id,))
                result = cursor.fetchone()
                
                if self.is_postgres:
                    acquired = result[0] if result else False
                else:
                    acquired = result[0] == 1 if result else False
                
                logger.info(f"Blockchain lock acquisition: {acquired}")
                return acquired
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error acquiring blockchain lock: {e}")
            return False
    
    def release_blockchain_lock(self):
        """
        Release the PostgreSQL advisory lock for blockchain initialization.
        """
        if not self.is_postgres:
            return
        
        try:
            import psycopg2
            import logging
            logger = logging.getLogger(__name__)
            
            lock_id = 123456789
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))
                logger.info("Blockchain lock released")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error releasing blockchain lock: {e}")

