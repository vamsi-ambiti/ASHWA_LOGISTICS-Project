import os
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir
root_dir = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ashwa.settings")

import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from logistics.models import Shipment, ShipmentTrackingUpdate, Enquiry, ContactMessage

def seed_database():
    print("[*] Seeding Ashwa Logistics Database...")

    # 1. Create or Update Admin Superuser
    admin_user, created = User.objects.get_or_create(username='admin', defaults={
        'email': 'admin@ashwalogistics.com',
        'first_name': 'Ashwa',
        'last_name': 'Administrator',
        'is_staff': True,
        'is_superuser': True
    })
    admin_user.set_password('admin123')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print(f"[OK] Admin account: username='admin', password='admin123' ({'Created' if created else 'Updated'})")

    # 2. Create Demo Customers
    customers_data = [
        ('rahul@example.com', 'Rahul', 'Sharma', 'customer123'),
        ('priya@example.com', 'Priya', 'Patel', 'customer123'),
        ('arun@example.com', 'Arun', 'Kumar', 'customer123')
    ]
    customers = []
    for email, first, last, pwd in customers_data:
        u, u_created = User.objects.get_or_create(username=email, defaults={
            'email': email,
            'first_name': first,
            'last_name': last
        })
        u.set_password(pwd)
        u.save()
        customers.append(u)
    print(f"[OK] Created {len(customers)} demo customers (password: 'customer123')")

    # 3. Create Sample Shipments
    shipments_data = [
        {
            'user': customers[0],
            'product_id': 'PROD88291043',
            'from_address': 'Mumbai, Maharashtra, India',
            'to_address': 'New Delhi, Delhi, India',
            'from_lat': Decimal('19.076090'),
            'from_lon': Decimal('72.877426'),
            'to_lat': Decimal('28.613939'),
            'to_lon': Decimal('77.209021'),
            'pickup_date': date.today() - timedelta(days=4),
            'estimated_delivery': date.today() - timedelta(days=1),
            'status': 'DELIVERED',
            'package_type': 'Heavy Freight',
            'weight_kg': Decimal('18.50'),
            'price': Decimal('1850.00'),
            'recipient_name': 'Amit Verma',
            'recipient_phone': '+91 98201 12345',
            'current_location': 'New Delhi, Delhi, India',
            'milestones': [
                ('CREATED', 'Mumbai Central Hub', 'Shipment order booked and confirmed.', -4),
                ('PENDING', 'Mumbai Sorting Facility', 'Package packed and awaiting departure.', -3),
                ('IN TRANSIT', 'Jaipur Highway Checkpoint', 'In transit to Northern Hub.', -2),
                ('OUT FOR DELIVERY', 'Delhi Okhla Hub', 'Out for final delivery with courier.', -1),
                ('DELIVERED', 'New Delhi Destination', 'Handed over to recipient Amit Verma. Signature confirmed.', -1)
            ]
        },
        {
            'user': customers[1],
            'product_id': 'PROD77412950',
            'from_address': 'Bengaluru, Karnataka, India',
            'to_address': 'Hyderabad, Telangana, India',
            'from_lat': Decimal('12.971599'),
            'from_lon': Decimal('77.594566'),
            'to_lat': Decimal('17.385044'),
            'to_lon': Decimal('78.486671'),
            'pickup_date': date.today() - timedelta(days=1),
            'estimated_delivery': date.today() + timedelta(days=2),
            'status': 'IN TRANSIT',
            'package_type': 'Express Document',
            'weight_kg': Decimal('0.75'),
            'price': Decimal('320.00'),
            'recipient_name': 'Kavita Reddy',
            'recipient_phone': '+91 94401 56789',
            'current_location': 'Anantapur Transit Center',
            'milestones': [
                ('CREATED', 'Bengaluru Koramangala Hub', 'Shipment initiated by customer.', -1),
                ('IN TRANSIT', 'Anantapur Transit Center', 'Arrived at intermediate distribution hub.', 0)
            ]
        },
        {
            'user': customers[2],
            'product_id': 'PROD55109342',
            'from_address': 'Chennai, Tamil Nadu, India',
            'to_address': 'Kolkata, West Bengal, India',
            'from_lat': Decimal('13.082680'),
            'from_lon': Decimal('80.270718'),
            'to_lat': Decimal('22.572646'),
            'to_lon': Decimal('88.363895'),
            'pickup_date': date.today(),
            'estimated_delivery': date.today() + timedelta(days=4),
            'status': 'CREATED',
            'package_type': 'Fragile Cargo',
            'weight_kg': Decimal('4.20'),
            'price': Decimal('890.00'),
            'recipient_name': 'Subhash Roy',
            'recipient_phone': '+91 98302 98765',
            'current_location': 'Chennai, Tamil Nadu, India',
            'milestones': [
                ('CREATED', 'Chennai Port Hub', 'Booking created. Carrier dispatch pending.', 0)
            ]
        }
    ]

    for s_data in shipments_data:
        milestones = s_data.pop('milestones')
        shipment, created = Shipment.objects.update_or_create(
            product_id=s_data['product_id'],
            defaults=s_data
        )
        if created:
            for status, loc, remarks, day_offset in milestones:
                ts = timezone.now() + timedelta(days=day_offset)
                ShipmentTrackingUpdate.objects.create(
                    shipment=shipment,
                    status=status,
                    location=loc,
                    remarks=remarks,
                    timestamp=ts,
                    updated_by=admin_user
                )

    print(f"[OK] Seeded {len(shipments_data)} sample shipments with full tracking history")

    # 4. Sample Enquiries
    enquiries_data = [
        {
            'name': 'Deepak Joshi',
            'email': 'deepak.joshi@example.com',
            'phone': '+91 98110 55443',
            'comment': 'I need quotation for daily recurring bulk logistics from Pune to Ahmedabad.',
            'status': 'PENDING'
        },
        {
            'name': 'Meera Sundaram',
            'email': 'meera.s@example.com',
            'phone': '+91 97400 33221',
            'comment': 'Regarding tracking PROD88291043: Received on time, thank you for the smooth service!',
            'status': 'RESOLVED',
            'admin_notes': 'Customer thanked us for prompt delivery.'
        }
    ]
    for eq in enquiries_data:
        Enquiry.objects.get_or_create(email=eq['email'], comment=eq['comment'], defaults=eq)
    print("[OK] Seeded sample enquiries")

    # 5. Sample Contact Messages
    messages_data = [
        {
            'name': 'Suresh Menon',
            'email': 'suresh.m@gmail.com',
            'phone': '+91 99887 66554',
            'message': 'Hello, do you offer refrigerated cold-chain transport for medicines?',
            'is_read': False
        },
        {
            'name': 'Ananya Roy',
            'email': 'ananya.roy@outlook.com',
            'phone': '+91 98765 43210',
            'message': 'Interested in enterprise corporate partnership for e-commerce deliveries.',
            'is_read': True,
            'admin_reply': 'Representative sent corporate deck via email.'
        }
    ]
    for msg in messages_data:
        ContactMessage.objects.get_or_create(email=msg['email'], message=msg['message'], defaults=msg)
    print("[OK] Seeded sample contact messages")

    print("\n[SUCCESS] Database seeding completed successfully!\n")

if __name__ == '__main__':
    seed_database()
