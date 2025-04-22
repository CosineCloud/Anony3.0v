#!/usr/bin/env python3
"""
Telegram Database Manager

This module provides utilities for managing SQLite databases used by the Telegram bot.
It includes functions to list, create, and modify database tables.
"""

import os
import sqlite3
import logging
import datetime
import traceback
from typing import List, Dict, Tuple, Optional, Union

# Define functions locally to avoid circular imports
def ANONY_NAME():
    """Generate an anonymous name."""
    import random
    import string
    prefix = random.choice(["Anonymous", "Unknown", "Hidden", "Secret", "Mysterious"])
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{suffix}"

def MEMBERSHIP_ID():
    """Generate a membership ID."""
    import random
    return f"92{random.randint(1000000, 9999999)}"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define SQLite data types with descriptions for user reference
SQLITE_TYPES = {
    "INTEGER": "Whole numbers (e.g., 1, 2, 3)",
    "REAL": "Floating point numbers (e.g., 1.0, 3.14)",
    "TEXT": "Text strings",
    "BLOB": "Binary data",
    "NULL": "Null value",
    "BOOLEAN": "Boolean values (0 or 1)",
    "DATE": "Date values (stored as TEXT)",
    "DATETIME": "Date and time values (stored as TEXT)",
    "TIME": "Time values (stored as TEXT)"
}

# Default database path
DEFAULT_DB_PATH = 'user_db.db'

def list_databases(directory: str = '.') -> List[str]:
    """
    List all SQLite database files in the specified directory.
    
    Args:
        directory: Directory to search for database files (default: current directory)
        
    Returns:
        List of database filenames
    """
    try:
        # Get all files in the directory
        all_files = os.listdir(directory)
        
        # Filter for SQLite database files (common extensions)
        db_extensions = ['.db', '.sqlite', '.sqlite3', '.db3']
        db_files = [
            file for file in all_files 
            if any(file.endswith(ext) for ext in db_extensions)
        ]
        
        if not db_files:
            logger.info(f"No database files found in {directory}")
        else:
            logger.info(f"Found {len(db_files)} database files in {directory}")
            
        return db_files
        
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return []

def connect_database(db_path: str = DEFAULT_DB_PATH) -> Tuple[Optional[sqlite3.Connection], Optional[sqlite3.Cursor]]:
    """
    Connect to a SQLite database.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Tuple of (connection, cursor) or (None, None) if connection fails
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        logger.info(f"Connected to database: {db_path}")
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None, None

def list_tables(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """
    List all tables in the specified database.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        List of table names
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return []
    
    try:
        # Query for all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(tables)} tables in {db_path}")
        conn.close()
        return tables
    except sqlite3.Error as e:
        logger.error(f"Error listing tables: {e}")
        conn.close()
        return []

def get_table_schema(table_name: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, str]]:
    """
    Get the schema for a specific table.
    
    Args:
        table_name: Name of the table
        db_path: Path to the database file
        
    Returns:
        List of column information dictionaries
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return []
    
    try:
        # Query for table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = []
        
        for row in cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default_value": row[4],
                "pk": row[5]
            })
        
        conn.close()
        return columns
    except sqlite3.Error as e:
        logger.error(f"Error getting schema for table {table_name}: {e}")
        conn.close()
        return []

def create_table(table_name: str, columns: List[Dict[str, str]], db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Create a new table in the database.
    
    Args:
        table_name: Name of the table to create
        columns: List of column definitions, each with 'name', 'type', and optional 'constraints'
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return False
    
    try:
        # Build the CREATE TABLE statement
        column_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if 'constraints' in col and col['constraints']:
                col_def += f" {col['constraints']}"
            column_defs.append(col_def)
        
        create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        create_stmt += ",\n".join(column_defs)
        create_stmt += "\n);"
        
        # Execute the statement
        cursor.execute(create_stmt)
        conn.commit()
        
        logger.info(f"Table '{table_name}' created successfully in {db_path}")
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error creating table {table_name}: {e}")
        conn.close()
        return False

def alter_table(table_name: str, operation: str, column_def: Dict[str, str] = None, 
                db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Alter an existing table in the database.
    
    Args:
        table_name: Name of the table to alter
        operation: Type of alteration ('ADD', 'DROP', 'RENAME')
        column_def: Column definition for ADD operations
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return False
    
    try:
        # Build the ALTER TABLE statement based on the operation
        if operation.upper() == 'ADD' and column_def:
            col_def = f"{column_def['name']} {column_def['type']}"
            if 'constraints' in column_def and column_def['constraints']:
                col_def += f" {column_def['constraints']}"
            
            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col_def};"
            
        elif operation.upper() == 'RENAME' and column_def:
            # SQLite supports renaming tables but not columns directly
            # For column renaming, we need to create a new table and copy data
            logger.error("Column renaming not supported directly in SQLite")
            conn.close()
            return False
            
        else:
            logger.error(f"Unsupported operation: {operation}")
            conn.close()
            return False
        
        # Execute the statement
        cursor.execute(alter_stmt)
        conn.commit()
        
        logger.info(f"Table '{table_name}' altered successfully in {db_path}")
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error altering table {table_name}: {e}")
        conn.close()
        return False

def delete_column(table_name: str, column_name: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Delete a column from a table. Since SQLite doesn't support DROP COLUMN directly,
    this function creates a new table without the column and copies the data.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to delete
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return False
    
    try:
        # Get the current table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Check if the column exists
        column_exists = False
        remaining_columns = []
        for col in columns:
            if col[1] != column_name:  # col[1] is the column name
                remaining_columns.append(col[1])
            else:
                column_exists = True
        
        if not column_exists:
            logger.error(f"Column '{column_name}' does not exist in table '{table_name}'")
            conn.close()
            return False
        
        if not remaining_columns:
            logger.error(f"Cannot delete the only column in table '{table_name}'")
            conn.close()
            return False
        
        # Create a new table without the column
        temp_table = f"{table_name}_temp"
        columns_str = ", ".join(remaining_columns)
        cursor.execute(f"CREATE TABLE {temp_table} AS SELECT {columns_str} FROM {table_name};")
        
        # Drop the original table
        cursor.execute(f"DROP TABLE {table_name};")
        
        # Rename the temp table to the original name
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name};")
        
        conn.commit()
        logger.info(f"Column '{column_name}' deleted from table '{table_name}'")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error deleting column '{column_name}' from table '{table_name}': {e}")
        conn.close()
        return False

def delete_row(table_name: str, condition: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Delete rows from a table that match the given condition.
    
    Args:
        table_name: Name of the table
        condition: WHERE clause condition (e.g., "user_id = 123")
        db_path: Path to the database file
        
    Returns:
        Number of rows deleted, or -1 if an error occurred
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return -1
    
    try:
        # Execute the DELETE statement
        cursor.execute(f"DELETE FROM {table_name} WHERE {condition};")
        rows_affected = cursor.rowcount
        
        conn.commit()
        logger.info(f"Deleted {rows_affected} rows from table '{table_name}' where {condition}")
        conn.close()
        return rows_affected
        
    except sqlite3.Error as e:
        logger.error(f"Error deleting rows from table '{table_name}': {e}")
        conn.close()
        return -1

def delete_table(table_name: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Delete a table from the database.
    
    Args:
        table_name: Name of the table to delete
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    conn, cursor = connect_database(db_path)
    if not conn or not cursor:
        return False
    
    try:
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        if not cursor.fetchone():
            logger.warning(f"Table '{table_name}' does not exist in database '{db_path}'")
            conn.close()
            return False
        
        # Execute the DROP TABLE statement
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        
        conn.commit()
        logger.info(f"Table '{table_name}' deleted successfully from database '{db_path}'")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error deleting table '{table_name}': {e}")
        conn.close()
        return False

def ensure_tables_exist():
    """
    Ensure that the required tables exist in the database.
    Creates them if they don't exist.
    """
    # Connect to the main database (user_db.db)
    conn, cursor = connect_database()
    if not conn or not cursor:
        logger.error("Failed to connect to database to ensure tables exist")
        return False
    
    try:
        # Check if 'users' table exists, create if not (with OTP_EXP field)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            USER_ID INTEGER PRIMARY KEY,
            PEER_ID TEXT,
            TYPE TEXT DEFAULT 'R48',
            STATUS TEXT DEFAULT 'OPEN',
            TIMER INTEGER DEFAULT 120,
            OTP TEXT,
            OTP_EXP DATETIME,
            ANONY_NAME TEXT,
            ANONY_PEER TEXT,
            CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        logger.info("Ensured users table exists in the main database")
        conn.close()
        
        # Now ensure user_def table exists in user_def.db
        user_def_db_path = 'user_def.db'
        
        try:
            # Check if file exists
            import os
            if not os.path.exists(user_def_db_path):
                logger.info(f"Creating new user_def database at {user_def_db_path}")
                
                # Try to create the directory if it doesn't exist
                os.makedirs(os.path.dirname(user_def_db_path), exist_ok=True)
            
            # Connect directly to user_def.db
            user_def_conn = sqlite3.connect(user_def_db_path)
            user_def_cursor = user_def_conn.cursor()
            
            # Create the user_def table if it doesn't exist - with only the required fields
            user_def_cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_def (
                USER_ID INTEGER PRIMARY KEY,
                MEMBERSHIP_ID TEXT UNIQUE,
                MEMBERSHIP_TYPE TEXT DEFAULT 'SILVER',
                CREDIT INTEGER DEFAULT 300
            )
            """)
            
            # Verify the table was created
            user_def_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_def'")
            table_exists = user_def_cursor.fetchone() is not None
            
            if table_exists:
                logger.info(f"user_def table created/verified successfully in {user_def_db_path}")
            else:
                logger.error(f"Failed to create user_def table in {user_def_db_path}")
                return False
            
            user_def_conn.commit()
            
            # Check if the file was created
            if os.path.exists(user_def_db_path):
                file_size = os.path.getsize(user_def_db_path)
                logger.info(f"user_def.db created successfully, size: {file_size} bytes")
            else:
                logger.error("Failed to create user_def.db file")
                return False
            
            user_def_conn.close()
            return True
        except Exception as e:
            logger.error(f"Error ensuring user_def table exists in {user_def_db_path}: {e}")
            return False
        
    except sqlite3.Error as e:
        logger.error(f"Error ensuring users table exists: {e}")
        conn.close()
        return False

def add_user_to_users_table(user_id: int) -> bool:
    """
    Add a user to the 'users' table.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    # Tables should already be ensured by the register_new_user function
    
    # Connect to the database
    conn, cursor = connect_database()
    if not conn or not cursor:
        return False
    
    try:
        # Check if user already exists
        cursor.execute("SELECT USER_ID FROM users WHERE USER_ID = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.info(f"User {user_id} already exists in users table")
            conn.close()
            return True
        
        # Generate anonymous name
        anony_name = ANONY_NAME()
        
        # Insert new user with TYPE set to R48
        cursor.execute("""
        INSERT INTO users (USER_ID, PEER_ID, TYPE, STATUS, TIMER, OTP, ANONY_NAME, ANONY_PEER)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, "", "R48", "OPEN", 120, "", anony_name, ""))
        
        conn.commit()
        logger.info(f"Added user {user_id} to users table with anonymous name {anony_name}")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error adding user to users table: {e}")
        conn.close()
        return False

def add_user_to_user_def_table(user_id: int) -> bool:
    """
    Add a user to the 'user_def' table in user_db.def database.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    # Define user_def database path
    user_def_db_path = 'user_def.db'
    
    # Ensure tables exist in both databases
    if not ensure_tables_exist():
        logger.error("Failed to ensure tables exist")
        return False
    
    # Connect to the user_def database
    conn, cursor = connect_database(user_def_db_path)
    if not conn or not cursor:
        logger.error(f"Failed to connect to {user_def_db_path} database")
        return False
    
    try:
        # Check if user already exists
        cursor.execute("SELECT USER_ID FROM user_def WHERE USER_ID = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.info(f"User {user_id} already exists in user_def table")
            conn.close()
            return True
        
        # Generate membership ID
        membership_id = MEMBERSHIP_ID()
        
        # Insert new user with only the required fields
        cursor.execute("""
        INSERT INTO user_def (USER_ID, MEMBERSHIP_ID, MEMBERSHIP_TYPE, CREDIT)
        VALUES (?, ?, ?, ?)
        """, (user_id, membership_id, "SILVER", 300))
        
        conn.commit()
        logger.info(f"Added user {user_id} to user_def table with membership ID {membership_id}")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error adding user to user_def table: {e}")
        conn.close()
        return False

def register_new_user(user_id: int) -> Dict[str, str]:
    """
    Register a new user in both database tables.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Dictionary with user information
    """
    # First ensure all tables exist in both databases
    if not ensure_tables_exist():
        logger.error("Failed to ensure tables exist")
        return {"status": "error", "message": "Failed to ensure tables exist"}
    
    # Add user to users table in user_db.db
    users_success = add_user_to_users_table(user_id)
    
    # Add user to user_def table in user_def.db
    # Use a direct approach for user_def.db to ensure it works
    user_def_success = False
    try:
        user_def_db_path = 'user_def.db'
        
        # Connect to user_def.db
        user_def_conn = sqlite3.connect(user_def_db_path)
        user_def_cursor = user_def_conn.cursor()
        
        # Check if user already exists
        user_def_cursor.execute("SELECT USER_ID FROM user_def WHERE USER_ID = ?", (user_id,))
        existing_user = user_def_cursor.fetchone()
        
        if existing_user:
            logger.info(f"User {user_id} already exists in user_def.db, skipping insert")
            user_def_success = True
        else:
            # Generate membership ID
            membership_id = MEMBERSHIP_ID()
            
            # Insert user into user_def table with only the required fields
            user_def_cursor.execute("""
            INSERT INTO user_def (USER_ID, MEMBERSHIP_ID, MEMBERSHIP_TYPE, CREDIT)
            VALUES (?, ?, ?, ?)
            """, (user_id, membership_id, "SILVER", 300))
            
            user_def_conn.commit()
            logger.info(f"Added user {user_id} to user_def.db with membership ID {membership_id}")
            user_def_success = True
        
        user_def_conn.close()
    except Exception as e:
        logger.error(f"Error adding user to user_def.db: {e}")
        user_def_success = False
    
    if not users_success or not user_def_success:
        logger.error(f"Failed to register user {user_id} in one or both tables")
        return {"status": "error", "message": "Failed to register user"}
    
    # Get user information from both databases
    try:
        # Get user data from users table in user_db.db
        conn, cursor = connect_database()
        if not conn or not cursor:
            return {"status": "error", "message": "Database connection failed"}
        
        cursor.execute("SELECT ANONY_NAME FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return {"status": "error", "message": "User not found in users table"}
        
        anony_name = user_data[0]
        conn.close()
        
        # Get user data from user_def table in user_def.db database
        user_def_db_path = 'user_def.db'
        
        # Connect directly to user_def.db
        user_def_conn = sqlite3.connect(user_def_db_path)
        user_def_cursor = user_def_conn.cursor()
        
        # Get user data
        user_def_cursor.execute("SELECT MEMBERSHIP_ID, MEMBERSHIP_TYPE, CREDIT FROM user_def WHERE USER_ID = ?", (user_id,))
        membership_data = user_def_cursor.fetchone()
        
        if not membership_data:
            user_def_conn.close()
            return {"status": "error", "message": "User not found in user_def table"}
        
        membership_id, membership_type, credit = membership_data
        user_def_conn.close()
        
        # Log successful retrieval
        logger.info(f"Successfully retrieved user data for user {user_id} from both databases")
        
        return {
            "status": "success",
            "user_id": str(user_id),
            "anony_name": anony_name,
            "membership_id": membership_id,
            "membership_type": membership_type,
            "credit": str(credit)
        }
        
    except sqlite3.Error as e:
        logger.error(f"Error retrieving user data: {e}")
        conn.close()
        return {"status": "error", "message": "Failed to retrieve user data"}

def parse_column_definition(column_str: str) -> Dict[str, str]:
    """
    Parse a column definition string into components.
    
    Args:
        column_str: String in format "name,type[,constraints]"
        
    Returns:
        Dictionary with column definition components
    """
    parts = [part.strip() for part in column_str.split(',')]
    
    if len(parts) < 2:
        raise ValueError("Column definition must include at least name and type")
    
    column_def = {
        'name': parts[0],
        'type': parts[1].upper()
    }
    
    # Check if the type is valid
    if column_def['type'] not in SQLITE_TYPES:
        valid_types = ', '.join(SQLITE_TYPES.keys())
        raise ValueError(f"Invalid column type. Valid types are: {valid_types}")
    
    # Add constraints if provided
    if len(parts) > 2:
        column_def['constraints'] = ' '.join(parts[2:])
    
    return column_def

def interactive_create_table():
    """
    Interactive function to create a new table by prompting the user for input.
    """
    print("\n=== Create New Database Table ===\n")
    
    # List available databases
    print("Available databases:")
    dbs = list_databases()
    for i, db in enumerate(dbs, 1):
        print(f"{i}. {db}")
    
    # Use default or select database
    db_path = input("\nEnter database path (or press Enter for user_db.db): ").strip()
    if not db_path:
        db_path = DEFAULT_DB_PATH
    
    # Get table name
    table_name = input("\nEnter table name: ").strip()
    if not table_name:
        print("Table name cannot be empty.")
        return
    
    # Display available column types
    print("\nAvailable column types:")
    for type_name, description in SQLITE_TYPES.items():
        print(f"  {type_name}: {description}")
    
    # Get column definitions
    print("\nEnter column definitions in format: name,type[,constraints]")
    print("Example: user_id,INTEGER,PRIMARY KEY")
    print("Enter a blank line when finished.")
    
    columns = []
    while True:
        column_str = input("\nColumn definition (or blank to finish): ").strip()
        if not column_str:
            break
        
        try:
            column_def = parse_column_definition(column_str)
            columns.append(column_def)
            print(f"Added column: {column_def['name']} ({column_def['type']})")
        except ValueError as e:
            print(f"Error: {e}")
    
    if not columns:
        print("No columns defined. Table creation cancelled.")
        return
    
    # Create the table
    success = create_table(table_name, columns, db_path)
    
    if success:
        print(f"\nTable '{table_name}' created successfully in {db_path}")
        
        # Show the table schema
        print("\nTable schema:")
        schema = get_table_schema(table_name, db_path)
        for col in schema:
            pk_str = "PRIMARY KEY" if col["pk"] else ""
            null_str = "NOT NULL" if col["notnull"] else "NULL"
            default = f"DEFAULT {col['default_value']}" if col['default_value'] is not None else ""
            print(f"  {col['name']} ({col['type']}) {pk_str} {null_str} {default}")
    else:
        print(f"\nFailed to create table '{table_name}'")

def interactive_delete_row():
    """
    Interactive function to delete rows from a table.
    """
    print("\n=== Delete Rows from Table ===\n")
    
    # Get database path
    db_path = input("Enter database path (or press Enter for user_db.db): ").strip()
    if not db_path:
        db_path = DEFAULT_DB_PATH
    
    # List tables in the database
    tables = list_tables(db_path)
    if not tables:
        print(f"No tables found in {db_path} or database doesn't exist.")
        return
    
    print(f"\nTables in {db_path}:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    # Get table name
    table_name = input("\nEnter table name: ").strip()
    if not table_name:
        print("Table name cannot be empty.")
        return
    
    if table_name not in tables:
        print(f"Table '{table_name}' not found in {db_path}.")
        return
    
    # Show table schema to help user construct the condition
    schema = get_table_schema(table_name, db_path)
    if schema:
        print(f"\nSchema for table '{table_name}':")
        for col in schema:
            pk_str = "PRIMARY KEY" if col["pk"] else ""
            null_str = "NOT NULL" if col["notnull"] else "NULL"
            print(f"  {col['name']} ({col['type']}) {pk_str} {null_str}")
    
    # Get condition for deletion
    print("\nEnter the condition for rows to delete.")
    print("Examples: 'user_id = 123', 'status = \"INACTIVE\"', 'last_login < \"2023-01-01\"'")
    condition = input("WHERE clause: ").strip()
    
    if not condition:
        print("Condition cannot be empty. Operation cancelled for safety.")
        return
    
    # Confirm deletion
    confirm = input(f"\nWARNING: This will delete all rows where {condition} from table '{table_name}'.\nType 'YES' to confirm: ").strip()
    
    if confirm != "YES":
        print("Operation cancelled.")
        return
    
    # Delete rows
    rows_deleted = delete_row(table_name, condition, db_path)
    
    if rows_deleted >= 0:
        print(f"\nSuccessfully deleted {rows_deleted} rows from table '{table_name}'.")
    else:
        print(f"\nFailed to delete rows from table '{table_name}'.")

def interactive_delete_column():
    """
    Interactive function to delete a column from a table.
    """
    print("\n=== Delete Column from Table ===\n")
    
    # Get database path
    db_path = input("Enter database path (or press Enter for user_db.db): ").strip()
    if not db_path:
        db_path = DEFAULT_DB_PATH
    
    # List tables in the database
    tables = list_tables(db_path)
    if not tables:
        print(f"No tables found in {db_path} or database doesn't exist.")
        return
    
    print(f"\nTables in {db_path}:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    # Get table name
    table_name = input("\nEnter table name: ").strip()
    if not table_name:
        print("Table name cannot be empty.")
        return
    
    if table_name not in tables:
        print(f"Table '{table_name}' not found in {db_path}.")
        return
    
    # Show table schema
    schema = get_table_schema(table_name, db_path)
    if not schema:
        print(f"Could not retrieve schema for table '{table_name}'.")
        return
    
    print(f"\nColumns in table '{table_name}':")
    for i, col in enumerate(schema, 1):
        pk_str = "PRIMARY KEY" if col["pk"] else ""
        print(f"{i}. {col['name']} ({col['type']}) {pk_str}")
    
    # Get column name
    column_name = input("\nEnter column name to delete: ").strip()
    if not column_name:
        print("Column name cannot be empty.")
        return
    
    # Check if column exists
    column_exists = False
    for col in schema:
        if col['name'] == column_name:
            column_exists = True
            break
    
    if not column_exists:
        print(f"Column '{column_name}' not found in table '{table_name}'.")
        return
    
    # Check if it's a primary key
    is_primary_key = False
    for col in schema:
        if col['name'] == column_name and col['pk']:
            is_primary_key = True
            break
    
    if is_primary_key:
        print(f"WARNING: Column '{column_name}' is a PRIMARY KEY. Deleting it may cause data integrity issues.")
    
    # Confirm deletion
    confirm = input(f"\nWARNING: This will permanently delete column '{column_name}' from table '{table_name}'.\nType 'YES' to confirm: ").strip()
    
    if confirm != "YES":
        print("Operation cancelled.")
        return
    
    # Delete column
    success = delete_column(table_name, column_name, db_path)
    
    if success:
        print(f"\nSuccessfully deleted column '{column_name}' from table '{table_name}'.")
    else:
        print(f"\nFailed to delete column '{column_name}' from table '{table_name}'.")

def interactive_delete_table():
    """
    Interactive function to delete a table from the database.
    """
    print("\n=== Delete Table from Database ===\n")
    
    # Get database path
    db_path = input("Enter database path (or press Enter for user_db.db): ").strip()
    if not db_path:
        db_path = DEFAULT_DB_PATH
    
    # List tables in the database
    tables = list_tables(db_path)
    if not tables:
        print(f"No tables found in {db_path} or database doesn't exist.")
        return
    
    # Display tables
    print(f"\nTables in {db_path}:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    # Get table name
    table_name = input("\nEnter table name to delete: ").strip()
    if not table_name:
        print("Table name cannot be empty.")
        return
    
    # Check if table exists
    if table_name not in tables:
        print(f"Table '{table_name}' not found in {db_path}.")
        return
    
    # Confirm deletion
    confirm = input(f"\nWARNING: This will permanently delete the table '{table_name}' and ALL its data.\nType 'YES' to confirm: ").strip()
    
    if confirm != "YES":
        print("Operation cancelled.")
        return
    
    # Delete table
    success = delete_table(table_name, db_path)
    
    if success:
        print(f"\nSuccessfully deleted table '{table_name}' from database '{db_path}'.")
    else:
        print(f"\nFailed to delete table '{table_name}' from database '{db_path}'.")

def main():
    """
    Main function to run the database manager interactively.
    """
    while True:
        print("\n=== Telegram Database Manager ===")
        print("1. List all databases")
        print("2. List tables in a database")
        print("3. Show table schema")
        print("4. Create a new table")
        print("5. Add column to existing table")
        print("6. Delete rows from table")
        print("7. Delete column from table")
        print("8. Delete table from database")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            print("\nDatabases in current directory:")
            dbs = list_databases()
            if dbs:
                for db in dbs:
                    print(f"  - {db}")
            else:
                print("  No databases found.")
                
        elif choice == '2':
            db_path = input("\nEnter database path (or press Enter for user_db.db): ").strip()
            if not db_path:
                db_path = DEFAULT_DB_PATH
                
            tables = list_tables(db_path)
            if tables:
                print(f"\nTables in {db_path}:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print(f"  No tables found in {db_path} or database doesn't exist.")
                
        elif choice == '3':
            db_path = input("\nEnter database path (or press Enter for user_db.db): ").strip()
            if not db_path:
                db_path = DEFAULT_DB_PATH
                
            table_name = input("Enter table name: ").strip()
            if table_name:
                schema = get_table_schema(table_name, db_path)
                if schema:
                    print(f"\nSchema for table '{table_name}':")
                    for col in schema:
                        pk_str = "PRIMARY KEY" if col["pk"] else ""
                        null_str = "NOT NULL" if col["notnull"] else "NULL"
                        default = f"DEFAULT {col['default_value']}" if col['default_value'] is not None else ""
                        print(f"  {col['name']} ({col['type']}) {pk_str} {null_str} {default}")
                else:
                    print(f"  Table '{table_name}' not found in {db_path} or database doesn't exist.")
            
        elif choice == '4':
            interactive_create_table()
            
        elif choice == '5':
            db_path = input("\nEnter database path (or press Enter for user_db.db): ").strip()
            if not db_path:
                db_path = DEFAULT_DB_PATH
                
            table_name = input("Enter table name: ").strip()
            if not table_name:
                print("Table name cannot be empty.")
                continue
                
            # Display available column types
            print("\nAvailable column types:")
            for type_name, description in SQLITE_TYPES.items():
                print(f"  {type_name}: {description}")
                
            column_str = input("\nColumn definition (name,type[,constraints]): ").strip()
            if column_str:
                try:
                    column_def = parse_column_definition(column_str)
                    success = alter_table(table_name, 'ADD', column_def, db_path)
                    
                    if success:
                        print(f"\nColumn '{column_def['name']}' added to table '{table_name}'")
                    else:
                        print(f"\nFailed to add column to table '{table_name}'")
                except ValueError as e:
                    print(f"Error: {e}")
        
        elif choice == '6':
            interactive_delete_row()
            
        elif choice == '7':
            interactive_delete_column()
            
        elif choice == '8':
            interactive_delete_table()
            
        elif choice == '9':
            print("\nExiting Database Manager. Goodbye!")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 9.")

def change_column_type(table_name: str, column_name: str, new_type: str, database_path: str = 'user_db.db') -> Dict[str, str]:
    """
    Change the data type of a column in a table.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to modify
        new_type: New data type for the column
        database_path: Path to the database file
        
    Returns:
        Dictionary with status and message
    """
    logger = logging.getLogger("telegram_db_manager")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Get the current table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            conn.close()
            return {
                "status": "error",
                "message": f"Table '{table_name}' does not exist"
            }
        
        # Check if the column exists
        column_exists = False
        column_definitions = []
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            
            if col_name == column_name:
                column_exists = True
                # Use the new type for this column
                column_definitions.append(f"{col_name} {new_type}")
                logger.info(f"Changing column '{col_name}' type from '{col_type}' to '{new_type}'")
            else:
                # Keep the original definition for other columns
                column_def = f"{col_name} {col_type}"
                if not_null:
                    column_def += " NOT NULL"
                if default_val is not None:
                    column_def += f" DEFAULT {default_val}"
                if pk:
                    column_def += " PRIMARY KEY"
                column_definitions.append(column_def)
        
        if not column_exists:
            conn.close()
            return {
                "status": "error",
                "message": f"Column '{column_name}' does not exist in table '{table_name}'"
            }
        
        # Create a new table with the updated schema
        temp_table = f"{table_name}_temp"
        column_names = [col[1] for col in columns]
        column_names_str = ", ".join(column_names)
        
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create the new table
        create_temp_table_sql = f"CREATE TABLE {temp_table} ({', '.join(column_definitions)})"
        cursor.execute(create_temp_table_sql)
        
        # Copy data from the old table to the new one
        cursor.execute(f"INSERT INTO {temp_table} SELECT {column_names_str} FROM {table_name}")
        
        # Drop the old table
        cursor.execute(f"DROP TABLE {table_name}")
        
        # Rename the new table to the original name
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
        
        # Commit the transaction
        conn.commit()
        
        logger.info(f"Successfully changed column '{column_name}' type to '{new_type}' in table '{table_name}'")
        
        conn.close()
        return {
            "status": "success",
            "message": f"Column '{column_name}' type changed to '{new_type}' in table '{table_name}'"
        }
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        logger.error(traceback.format_exc())
        
        # Try to rollback if connection exists
        try:
            if conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        
        # Try to rollback if connection exists
        try:
            if conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

if __name__ == "__main__":
    main()