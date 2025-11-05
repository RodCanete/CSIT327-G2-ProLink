"""
Diagnose the exact decimal issue Django is having
"""
import sqlite3
import decimal
import os

def main():
    db_path = 'prolink/db.sqlite3' if os.path.exists('prolink/db.sqlite3') else 'db.sqlite3'
    
    print("="*60)
    print("Diagnosing Decimal Conversion Issues")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, price FROM requests_request")
    rows = cursor.fetchall()
    
    print(f"\nFound {len(rows)} requests\n")
    
    for req_id, title, price_raw in rows:
        print(f"\nRequest ID {req_id}: {title}")
        print(f"  Raw price value: {repr(price_raw)}")
        print(f"  Type: {type(price_raw)}")
        
        if price_raw is not None:
            # Try different conversions
            try:
                dec = decimal.Decimal(str(price_raw))
                print(f"  ✓ Decimal conversion: {dec}")
                
                # Try quantizing like Django does (2 decimal places for DecimalField(max_digits=10, decimal_places=2))
                quantize_value = decimal.Decimal('0.01')
                quantized = dec.quantize(quantize_value)
                print(f"  ✓ Quantized (2 decimals): {quantized}")
                
            except decimal.InvalidOperation as e:
                print(f"  ✗ Decimal error: {e}")
                print(f"  → This record needs fixing!")
                
                # Fix it
                cursor.execute("UPDATE requests_request SET price = ? WHERE id = ?", (None, req_id))
                print(f"  ✓ Fixed: Set to NULL")
            except Exception as e:
                print(f"  ✗ Other error: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("Diagnosis complete!")
    print("="*60)

if __name__ == "__main__":
    main()
