#!/usr/bin/env python3
"""
Setup script to download and prepare the Northwind database.

This script supports two deployment options:
1. Local SQLite database (default) - for development and testing
2. IT-managed PostgreSQL database - for production deployments

For PostgreSQL setup, you'll need to request an IT-provisioned database.
See README.md for instructions on requesting PostgreSQL access.
"""

import sys
import urllib.request
import sqlite3
import argparse
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def download_northwind_database(lite_version=True, max_rows_per_table=1000):
    """Download the Northwind SQLite database from GitHub and optionally create a lite version."""
    database_dir = Path("database")
    database_dir.mkdir(exist_ok=True)

    database_path = database_dir / "northwind.db"
    temp_database_path = database_dir / "northwind_full_temp.db"

    # If database already exists, ask user if they want to overwrite
    if database_path.exists():
        print(f"Overwriting existing database {database_path}")

    # Download URL for the Northwind SQLite database from jpwhite3/northwind-SQLite3
    # Try multiple sources in case one is unavailable
    urls = [
        "https://github.com/jpwhite3/northwind-SQLite3/raw/main/dist/northwind.db",
        "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db",
    ]

    # Try downloading from multiple sources
    download_target = temp_database_path if lite_version else database_path
    
    for i, url in enumerate(urls):
        print(f"Downloading Northwind database from {url}...")

        try:
            # Download the database file
            urllib.request.urlretrieve(url, download_target)
            print(f"✅ Successfully downloaded Northwind database")

            if lite_version:
                print(f"📉 Creating lite version (max {max_rows_per_table} rows per table)...")
                create_lite_database(temp_database_path, database_path, max_rows_per_table)
                # Clean up temp file
                temp_database_path.unlink()
                print(f"✅ Lite database created at {database_path}")
            
            # Verify the database is valid
            verify_sqlite_database(database_path)

            return database_path

        except Exception as e:
            print(f"❌ Error downloading from source {i+1}: {e}")
            # Clean up partial download
            if download_target.exists():
                download_target.unlink()
            if database_path.exists() and lite_version:
                database_path.unlink()

            # If this was the last URL, return None
            if i == len(urls) - 1:
                print("❌ All download sources failed!")
                return None
            else:
                print("Trying next source...")
                continue


def create_lite_database(source_db, target_db, max_rows=1000):
    """Create a lite version of the database with limited rows per table."""
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # Get all tables
    source_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = source_cursor.fetchall()
    
    for table_name, create_sql in tables:
        # Create table in target database
        target_cursor.execute(create_sql)
        
        # Copy limited rows
        source_cursor.execute(f'SELECT * FROM "{table_name}" LIMIT {max_rows}')
        rows = source_cursor.fetchall()
        
        if rows:
            columns = [desc[0] for desc in source_cursor.description]
            placeholders = ','.join(['?'] * len(columns))
            columns_str = ','.join([f'"{col}"' for col in columns])
            
            insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            target_cursor.executemany(insert_sql, rows)
            print(f"   - {table_name}: {len(rows)} rows")
    
    target_conn.commit()
    source_conn.close()
    target_conn.close()


def verify_sqlite_database(database_path):
    """Verify that the downloaded SQLite database is valid and contains expected tables."""
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Check for expected Northwind tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "Categories",
            "Customers",
            "Employees",
            "Order Details",
            "Orders",
            "Products",
            "Suppliers",
            "Territories",
            "EmployeeTerritories",
            "Regions",
            "Shippers",
        ]

        missing_tables = [table for table in expected_tables if table not in tables]

        if missing_tables:
            print(f"⚠️  Warning: Some expected tables are missing: {missing_tables}")
        else:
            print("✅ Database verification successful - all expected tables found")

        # Print some basic stats
        cursor.execute("SELECT COUNT(*) FROM Products")
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Orders")
        order_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Customers")
        customer_count = cursor.fetchone()[0]

        print("📊 Database contains:")
        print(f"   - {product_count} products")
        print(f"   - {order_count} orders")
        print(f"   - {customer_count} customers")

        conn.close()

    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        raise


def setup_postgres_database(connection_string, lite_version=True, max_rows_per_table=1000):
    """
    Setup Northwind database in a PostgreSQL instance.
    
    This function:
    1. Downloads the Northwind SQLite database temporarily
    2. Migrates the data to PostgreSQL (using 'public' schema)
    3. Verifies the PostgreSQL tables
    
    Args:
        connection_string: PostgreSQL connection string 
                          (e.g., postgresql://user:password@host:port/dbname)
        lite_version: If True, limits rows per table for faster setup
        max_rows_per_table: Maximum rows to copy per table (default: 1000)
    """
    try:
        import psycopg2
        from io import StringIO
    except ImportError:
        print("❌ Error: psycopg2 is required for PostgreSQL support")
        print("Install it with: pip install psycopg2-binary")
        sys.exit(1)

    # Northwind database will be created in the 'public' schema (PostgreSQL default)
    schema = "public"
    
    print(f"🚀 Setting up Northwind database in PostgreSQL...")
    print(f"📍 Connection: {mask_connection_string(connection_string)}")
    print(f"📂 Schema: {schema} (default)")
    if lite_version:
        print(f"⚡ Lite version: max {max_rows_per_table} rows per table")

    # Step 1: Download SQLite database to temporary location
    print("\n📥 Step 1: Downloading Northwind SQLite database...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "northwind_temp.db"
        
        urls = [
            "https://github.com/jpwhite3/northwind-SQLite3/raw/main/dist/northwind.db",
            "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db",
        ]
        
        downloaded = False
        for i, url in enumerate(urls):
            try:
                print(f"   Trying source {i+1}...")
                urllib.request.urlretrieve(url, temp_db_path)
                print(f"   ✅ Downloaded successfully")
                downloaded = True
                break
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                if i == len(urls) - 1:
                    print("❌ All download sources failed!")
                    return False
        
        if not downloaded:
            return False

        # Step 2: Connect to PostgreSQL
        print("\n🔌 Step 2: Connecting to PostgreSQL...")
        try:
            pg_conn = psycopg2.connect(connection_string)
            pg_conn.autocommit = False
            pg_cursor = pg_conn.cursor()
            print("   ✅ Connected successfully")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False

        # Step 3: Create schema if it doesn't exist
        print(f"\n📂 Step 3: Setting up schema '{schema}'...")
        try:
            pg_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            pg_cursor.execute(f"SET search_path TO {schema}")
            pg_conn.commit()
            print(f"   ✅ Schema ready")
        except Exception as e:
            print(f"   ❌ Schema setup failed: {e}")
            pg_conn.rollback()
            pg_conn.close()
            return False

        # Step 4: Read SQLite database
        print("\n📖 Step 4: Reading SQLite database structure...")
        try:
            sqlite_conn = sqlite3.connect(temp_db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get all table definitions
            sqlite_cursor.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables_info = sqlite_cursor.fetchall()
            print(f"   ✅ Found {len(tables_info)} tables")
            
        except Exception as e:
            print(f"   ❌ Failed to read SQLite: {e}")
            pg_conn.close()
            sqlite_conn.close()
            return False

        # Step 5: Migrate tables
        print("\n🔄 Step 5: Migrating tables to PostgreSQL...")
        try:
            # First pass: Create all tables without foreign key constraints
            print("   📝 Creating table structures...")
            for table_name, create_sql in tables_info:
                print(f"      Creating {table_name}...")
                
                # Convert SQLite CREATE TABLE to PostgreSQL
                pg_create_sql = convert_sqlite_to_postgres(create_sql, schema)
                
                # Remove foreign key constraints temporarily
                pg_create_sql_no_fk = remove_foreign_keys(pg_create_sql)
                
                # Drop table if exists and create new one
                pg_cursor.execute(f'DROP TABLE IF EXISTS {schema}."{table_name}" CASCADE')
                try:
                    pg_cursor.execute(pg_create_sql_no_fk)
                except Exception as e:
                    print(f"\n❌ Error creating {table_name}:")
                    print(f"SQL was:\n{pg_create_sql_no_fk}\n")
                    raise
            
            pg_conn.commit()
            print("   ✅ All table structures created")
            
            # Second pass: Copy data using PostgreSQL COPY (much faster)
            print("   📊 Copying data...")
            for table_name, create_sql in tables_info:
                # Limit rows if lite version
                if lite_version:
                    sqlite_cursor.execute(f'SELECT * FROM "{table_name}" LIMIT {max_rows_per_table}')
                else:
                    sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = sqlite_cursor.fetchall()
                
                if rows:
                    # Get column names
                    columns = [desc[0] for desc in sqlite_cursor.description]
                    columns_str = ','.join([f'"{col}"' for col in columns])
                    
                    # Use PostgreSQL COPY for bulk insert (10-100x faster than INSERT)
                    csv_buffer = StringIO()
                    for row in rows:
                        # Convert each value, handling binary data
                        processed_row = []
                        for val in row:
                            if val is None:
                                processed_row.append('\\N')
                            elif isinstance(val, bytes):
                                # Convert binary data to PostgreSQL bytea hex format
                                processed_row.append('\\\\x' + val.hex())
                            else:
                                # Escape special characters for COPY
                                str_val = str(val).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
                                processed_row.append(str_val)
                        csv_buffer.write('\t'.join(processed_row) + '\n')
                    
                    csv_buffer.seek(0)
                    # PostgreSQL COPY command - if in public schema, just use table name
                    # copy_from adds quotes automatically, so we don't need them
                    pg_cursor.copy_from(
                        csv_buffer, 
                        table_name,
                        sep='\t',
                        null='\\N',
                        columns=columns
                    )
                    print(f"      ✅ {table_name}: {len(rows)} rows")
                else:
                    print(f"      ℹ️  {table_name}: empty")
            
            pg_conn.commit()
            print("   ✅ All data migrated successfully")
            
        except Exception as e:
            print(f"   ❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            pg_conn.rollback()
            pg_conn.close()
            sqlite_conn.close()
            return False

        # Step 6: Verify PostgreSQL database
        print("\n✅ Step 6: Verifying PostgreSQL database...")
        try:
            verify_postgres_database(pg_conn, schema)
        except Exception as e:
            print(f"   ⚠️  Verification warning: {e}")

        # Cleanup
        sqlite_conn.close()
        pg_conn.close()
        print("\n🎉 PostgreSQL database setup completed successfully!")
        return True


def remove_foreign_keys(sql):
    """Remove FOREIGN KEY constraints from CREATE TABLE statement."""
    import re
    
    # Split into lines for better control
    lines = sql.split('\n')
    filtered_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        # Skip lines that contain FOREIGN KEY
        if re.search(r'FOREIGN\s+KEY', line, re.IGNORECASE):
            skip_next = True
            continue
        # Skip ON DELETE/UPDATE lines that are part of FOREIGN KEY
        if skip_next and re.search(r'ON\s+(DELETE|UPDATE)', line, re.IGNORECASE):
            continue
        else:
            skip_next = False
            
        # Only add non-empty lines
        if line.strip():
            filtered_lines.append(line)
    
    result = '\n'.join(filtered_lines)
    
    # Clean up trailing commas before closing parenthesis
    result = re.sub(r',\s*\)', ')', result)
    # Clean up multiple consecutive commas
    result = re.sub(r',\s*,', ',', result)
    
    return result


def convert_sqlite_to_postgres(sqlite_sql, schema):
    """Convert SQLite CREATE TABLE statement to PostgreSQL."""
    import re
    
    # Replace SQLite square brackets with PostgreSQL double quotes first
    # Handle: [Table Name] -> "Table Name"
    pg_sql = re.sub(r'\[([^\]]+)\]', r'"\1"', sqlite_sql)
    
    # Replace backticks with double quotes
    # Handle: `TableName` -> "TableName"
    pg_sql = pg_sql.replace('`', '"')
    
    # Replace AUTOINCREMENT with SERIAL for PostgreSQL
    # INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL PRIMARY KEY
    pg_sql = re.sub(
        r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT',
        'SERIAL PRIMARY KEY',
        pg_sql,
        flags=re.IGNORECASE
    )
    
    # Also handle just AUTOINCREMENT without PRIMARY KEY
    pg_sql = re.sub(r'\s+AUTOINCREMENT', '', pg_sql, flags=re.IGNORECASE)
    
    # Basic type conversions
    pg_sql = pg_sql.replace("BLOB", "BYTEA")
    pg_sql = re.sub(r'\bDATETIME\b', 'TIMESTAMP', pg_sql, flags=re.IGNORECASE)
    
    # Handle table name with schema - match various quote styles
    match = re.search(r'CREATE TABLE\s+["\']?([^"\'(\s]+)["\']?\s*\(', pg_sql, re.IGNORECASE)
    if match:
        table_name = match.group(1)
        # Remove any remaining quotes from table name
        table_name = table_name.strip('"').strip("'").strip("`")
        pg_sql = re.sub(
            r'CREATE TABLE\s+["\']?[^"\'(\s]+["\']?\s*\(',
            f'CREATE TABLE {schema}."{table_name}" (',
            pg_sql,
            flags=re.IGNORECASE,
            count=1
        )
    
    return pg_sql


def verify_postgres_database(connection, schema="public"):
    """Verify that the PostgreSQL database contains expected tables."""
    try:
        cursor = connection.cursor()
        
        # Check for expected Northwind tables
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema}' 
            AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            "Categories",
            "Customers",
            "Employees",
            "Order Details",
            "Orders",
            "Products",
            "Suppliers",
            "Territories",
            "EmployeeTerritories",
            "Regions",
            "Shippers",
        ]
        
        # Case-insensitive comparison
        tables_lower = [t.lower() for t in tables]
        missing_tables = [t for t in expected_tables if t.lower() not in tables_lower]
        
        if missing_tables:
            print(f"   ⚠️  Warning: Some expected tables are missing: {missing_tables}")
        else:
            print("   ✅ All expected tables found")
        
        # Print some basic stats
        cursor.execute(f'SELECT COUNT(*) FROM {schema}."Products"')
        product_count = cursor.fetchone()[0]
        
        cursor.execute(f'SELECT COUNT(*) FROM {schema}."Orders"')
        order_count = cursor.fetchone()[0]
        
        cursor.execute(f'SELECT COUNT(*) FROM {schema}."Customers"')
        customer_count = cursor.fetchone()[0]
        
        print("   📊 Database contains:")
        print(f"      - {product_count} products")
        print(f"      - {order_count} orders")
        print(f"      - {customer_count} customers")
        
    except Exception as e:
        print(f"   ❌ Error verifying database: {e}")
        raise


def mask_connection_string(conn_str):
    """Mask password in connection string for logging."""
    try:
        parsed = urlparse(conn_str)
        if parsed.password:
            masked = conn_str.replace(parsed.password, "****")
            return masked
        return conn_str
    except:
        return "postgresql://****:****@****:****/****"


def print_postgres_instructions():
    """Print instructions for requesting an IT-provisioned PostgreSQL database."""
    print("\n" + "="*80)
    print("📚 HOW TO REQUEST AN IT-PROVISIONED POSTGRESQL DATABASE")
    print("="*80)
    print("""
To use PostgreSQL with this application, you need to request a database from IT:

1. 🎫 Submit a request through your organization's IT ticketing system
   - Specify: PostgreSQL database for NAT React agent blueprint's Northwind database
   - Required permissions: CREATE, SELECT, INSERT, UPDATE, DELETE on tables
   - Note: Northwind tables will be created in the 'public' schema

2. 📝 You will receive connection details:
   - Host: e.g., wfo-astra-prd-rw.db.nvidia.com
   - Port: typically 5432
   - Database name: e.g., astra_starterpacks
   - Username and password

3. 🔧 Run this script with your connection string:
   python setup_database.py --postgres \\
       --connection-string "postgresql://user:password@host:port/dbname"

4. ⚙️  Update your config-react.yaml and env.sh:
   - Set PostgreSQL environment variables in env.sh (see env_template.sh)
   - Uncomment the PostgreSQL connection line in config-react.yaml

Example Connection String:
postgresql://astra_adm:mypassword@wfo-astra-prd-rw.db.nvidia.com:5432/astra_starterpacks

Security Note: Store credentials securely using environment variables!
""")
    print("="*80 + "\n")


def main():
    """Main function to set up the Northwind database."""
    parser = argparse.ArgumentParser(
        description="Setup Northwind database for NAT React agent blueprint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup local SQLite database (default)
  python setup_database.py

  # Setup PostgreSQL database
  python setup_database.py --postgres \\
      --connection-string "postgresql://user:pass@host:5432/dbname"

  # Show PostgreSQL setup instructions
  python setup_database.py --postgres-help
        """
    )
    
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Setup Northwind database in PostgreSQL instead of local SQLite"
    )
    
    parser.add_argument(
        "--connection-string",
        type=str,
        help="PostgreSQL connection string (e.g., postgresql://user:pass@host:5432/dbname)"
    )
    
    parser.add_argument(
        "--postgres-help",
        action="store_true",
        help="Show instructions for requesting IT-provisioned PostgreSQL database"
    )
    
    args = parser.parse_args()
    
    # Show PostgreSQL instructions if requested
    if args.postgres_help:
        print_postgres_instructions()
        sys.exit(0)
    
    print("🚀 Setting up Northwind database for NAT React agent blueprint...")
    print()
    
    if args.postgres:
        # PostgreSQL setup
        if not args.connection_string:
            print("❌ Error: --connection-string is required for PostgreSQL setup")
            print("\nUse --postgres-help for instructions on requesting a PostgreSQL database")
            sys.exit(1)
        
        success = setup_postgres_database(args.connection_string, lite_version=True, max_rows_per_table=1000)
        
        if success:
            print("\n✅ PostgreSQL database setup completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Configure PostgreSQL environment variables in env.sh (see env_template.sh)")
            print("   2. Update config-react.yaml to use PostgreSQL connection")
            print("   3. Uncomment the PostgreSQL db_connection_string_or_path line in config-react.yaml")
            print("   4. Source your env.sh: source env.sh")
            print("\nYou can now run the NAT blueprint application with PostgreSQL!")
        else:
            print("\n❌ PostgreSQL database setup failed!")
            sys.exit(1)
    else:
        # SQLite setup (default)
        print("📍 Setting up local SQLite database (use --postgres for PostgreSQL)")
        print("⚡ Creating lite version for faster setup...")
        print()
        
        database_path = download_northwind_database(lite_version=True, max_rows_per_table=1000)
        
        if database_path:
            print("\n✅ SQLite database setup completed successfully!")
            print(f"\n📂 Database location: {database_path}")
            print("\n📝 Configuration:")
            print(f"   db_connection_string_or_path: \"{database_path}\"")
            print("\nYou can now run the NAT blueprint application.")
            print("\n💡 Tip: Use --postgres-help to learn about PostgreSQL setup for production")
        else:
            print("\n❌ SQLite database setup failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
