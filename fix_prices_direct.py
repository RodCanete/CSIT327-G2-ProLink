"""
Direct SQLite script to fix invalid decimal values
This bypasses Django entirely and works directly with SQLite
Run from prolink directory: python fix_prices_direct.py
"""
import sqlite3
import os
import decimal

def main():
    # Find the database file - try multiple possible locations
    db_paths = [
        'db.sqlite3',
        'prolink/db.sqlite3',
        os.path.join('prolink', 'db.sqlite3')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"✗ Error: Database file not found!")
        print("  Searched in:")
        for path in db_paths:
            print(f"    - {path}")
        print("\n  Current directory:", os.getcwd())
        return
    
    print("="*60)
    print("Direct SQLite Fix for Invalid Decimal Values")
    print("="*60)
    print(f"Database: {db_path}\n")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all requests
        cursor.execute("SELECT id, title, price FROM requests_request")
        rows = cursor.fetchall()
        
        total_count = len(rows)
        print(f"Total requests: {total_count}\n")
        
        fixed_count = 0
        valid_count = 0
        
        for req_id, title, price_raw in rows:
            # Check if price is valid
            if price_raw is None:
                valid_count += 1
                print(f"✓ ID {req_id}: NULL price (valid)")
            else:
                try:
                    # Try to convert to decimal
                    decimal.Decimal(str(price_raw))
                    valid_count += 1
                    print(f"✓ ID {req_id}: Valid price = {price_raw}")
                except (decimal.InvalidOperation, ValueError):
                    # Invalid price found
                    print(f"\n⚠ ID {req_id} (\"{title}\"): INVALID price = {repr(price_raw)}")
                    
                    # Fix it by setting to NULL
                    cursor.execute(
                        "UPDATE requests_request SET price = NULL WHERE id = ?",
                        (req_id,)
                    )
                    fixed_count += 1
                    print(f"  → Fixed: Set to NULL\n")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✓ Total requests: {total_count}")
        print(f"✓ Valid prices: {valid_count}")
        print(f"✓ Fixed invalid prices: {fixed_count}")
        
        if fixed_count > 0:
            print("\n✓ Database updated successfully!")
            print("  You can now run: python manage.py runserver")
        else:
            print("\n✓ No invalid prices found - database is clean!")
        
        print("="*60)
        
    except sqlite3.Error as e:
        print(f"\n✗ SQLite error: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()
