"""
Management command to fix invalid decimal values in the Request model
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
import decimal


class Command(BaseCommand):
    help = 'Fixes invalid decimal values in Request price fields'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('Scanning for invalid price values using raw SQL...')
        self.stdout.write('='*60)
        
        fixed_count = 0
        total_count = 0
        
        try:
            with connection.cursor() as cursor:
                # First, get count of all requests
                cursor.execute("SELECT COUNT(*) FROM requests_request")
                total_count = cursor.fetchone()[0]
                self.stdout.write(f'\nTotal requests in database: {total_count}')
                
                # Get all records with their raw price values
                cursor.execute("SELECT id, title, price FROM requests_request")
                rows = cursor.fetchall()
                
                self.stdout.write('\nChecking each record...\n')
                
                for row in rows:
                    req_id, title, price_raw = row
                    
                    # Check if price is problematic
                    needs_fix = False
                    
                    if price_raw is not None:
                        try:
                            # Try to convert the raw value to decimal
                            decimal.Decimal(str(price_raw))
                            # If successful, it's valid
                            self.stdout.write(f'  ✓ ID {req_id}: Valid price')
                        except (decimal.InvalidOperation, ValueError, TypeError) as e:
                            # Found invalid price
                            needs_fix = True
                            self.stdout.write(
                                self.style.WARNING(
                                    f'\n  ⚠ ID {req_id} ("{title}"): Invalid price = {repr(price_raw)}'
                                )
                            )
                            self.stdout.write(f'     Error: {str(e)}')
                    else:
                        self.stdout.write(f'  ✓ ID {req_id}: Price is NULL (valid)')
                    
                    # Fix if needed
                    if needs_fix:
                        try:
                            with transaction.atomic():
                                cursor.execute(
                                    "UPDATE requests_request SET price = NULL WHERE id = ?",
                                    [req_id]
                                )
                                fixed_count += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'     → Fixed: Set price to NULL'
                                    )
                                )
                        except Exception as save_error:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'     → Error fixing: {str(save_error)}'
                                )
                            )
                
                # Commit the changes
                connection.commit()
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nDatabase error: {str(e)}')
            )
            return
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Scanned {total_count} requests'))
        self.stdout.write(self.style.SUCCESS(f'✓ Fixed {fixed_count} invalid price values'))
        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No invalid prices found!'))
        self.stdout.write('='*60)
