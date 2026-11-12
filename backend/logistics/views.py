import json
import random
import string
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods

from .models import (
    Shipment,
    ShipmentTrackingUpdate,
    Enquiry,
    ContactMessage,
)

from django.core.mail import send_mail
from django.conf import settings

def csrf_api(request):
    return JsonResponse({'csrfToken': get_token(request)})

def api_index(request):
    return JsonResponse({
        'service': 'Ashwa Logistics Backend API',
        'status': 'online',
        'django_admin': 'http://127.0.0.1:8000/admin/',
        'frontend_website': 'http://127.0.0.1:5500/',
        'endpoints': {
            'csrf': '/api/csrf/',
            'me': '/api/me/',
            'shipments': '/api/shipments/',
            'tracking': '/api/shipments/<product_id>/',
            'my_shipments': '/api/my-shipments/',
            'enquiries': '/api/enquiries/',
            'contact': '/api/contact/',
            'admin_dashboard': '/api/admin/dashboard/'
        }
    })

# Helper to render pages with CSRF cookie
def page(template):
    @ensure_csrf_cookie
    def view(request):
        return render(request, template)
    return view

home = page('index.html')
login_page = page('login.html')
signup_page = page('signup.html')
enquiry_page = page('enquiry.html')
contact_page = page('contact.html')
admin_login_page = page('admin_login.html')

@ensure_csrf_cookie
def admin_dashboard_page(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/')
    return render(request, 'admin_dashboard.html')

def get_json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return {}

def serialize_tracking_update(u):
    return {
        'id': u.id,
        'status': u.status,
        'location': u.location,
        'remarks': u.remarks,
        'timestamp': u.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_by': u.updated_by.username if u.updated_by else 'System'
    }

def serialize_shipment(s, include_history=False):
    data = {
        'id': s.id,
        'product_id': s.product_id,
        'customer_name': s.user.get_full_name() or s.user.username,
        'customer_email': s.user.email,
        'from_address': s.from_address,
        'to_address': s.to_address,
        'from_lat': float(s.from_lat),
        'from_lon': float(s.from_lon),
        'to_lat': float(s.to_lat),
        'to_lon': float(s.to_lon),
        'pickup_date': s.pickup_date.isoformat(),
        'estimated_delivery': s.estimated_delivery.isoformat(),
        'status': s.status,
        'package_type': s.package_type,
        'weight_kg': float(s.weight_kg),
        'price': float(s.price),
        'recipient_name': s.recipient_name,
        'recipient_phone': s.recipient_phone,
        'current_location': s.current_location or s.from_address,
        'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M')
    }
    if include_history:
        data['tracking_history'] = [
            serialize_tracking_update(u) for u in s.tracking_updates.all()
        ]
    return data

# ==========================================
# AUTHENTICATION & PROFILE APIS
# ==========================================

from django.contrib.sessions.models import Session

def get_authenticated_user(request):
    """
    Authenticate a normal customer/admin request using:
    1. Standard Django session cookie (request.user)
    2. Django session token (X-Session-Token header) validated against Session store
    """
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and user.is_active:
        return user

    token = request.headers.get('X-Session-Token') or request.META.get('HTTP_X_SESSION_TOKEN')
    if token:
        try:
            session = Session.objects.filter(session_key=token, expire_date__gt=timezone.now()).first()
            if session:
                data = session.get_decoded()
                user_id = data.get('_auth_user_id')
                if user_id:
                    matched_user = User.objects.filter(pk=user_id, is_active=True).first()
                    if matched_user:
                        request.user = matched_user
                        return matched_user
        except Exception:
            pass

    return None

def me_api(request):
    user = get_authenticated_user(request)
    if user:
        shipment_count = Shipment.objects.filter(user=user).count()
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'shipment_count': shipment_count
            }
        })
    return JsonResponse({'authenticated': False})

@csrf_exempt
def signup_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    name = str(d.get('name', '')).strip()
    email = str(d.get('email', '')).strip().lower()
    password = str(d.get('password', ''))

    if not name or not email or not password:
        return JsonResponse({'error': 'All fields are required.'}, status=400)
    
    if len(password) < 6:
        return JsonResponse({'error': 'Password must be at least 6 characters.'}, status=400)

    if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'error': 'An account with this email already exists.'}, status=400)

    parts = name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    # Auto-login after signup
    login(request, user)
    request.session.save()

    return JsonResponse({
        'message': 'Account created successfully',
        'token': request.session.session_key,
        'user': {
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'is_staff': user.is_staff
        }
    })

@csrf_exempt
def login_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    login_id = str(d.get('email', '')).strip().lower()
    password = str(d.get('password', ''))

    # Authenticate by username or email
    user = authenticate(request, username=login_id, password=password)
    if not user:
        # Check if email corresponds to a username
        try:
            matched_user = User.objects.get(email__iexact=login_id)
            user = authenticate(request, username=matched_user.username, password=password)
        except User.DoesNotExist:
            pass

    if not user:
        return JsonResponse({'error': 'Invalid email or password!'}, status=400)
    
    if not user.is_active:
        return JsonResponse({'error': 'This account has been disabled. Contact support.'}, status=403)

    login(request, user)
    request.session.save()

    return JsonResponse({
        'message': 'Login successful',
        'token': request.session.session_key,
        'user': {
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'is_staff': user.is_staff
        }
    })

@csrf_exempt
def logout_api(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})

# ==========================================
# CUSTOMER SHIPMENT APIS
# ==========================================

@csrf_exempt
def shipment_create_api(request):
    user = get_authenticated_user(request)
    if not user:
        return JsonResponse({'error': 'Please login first to book a shipment.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    try:
        from_address = str(d.get('from_address', '')).strip()
        to_address = str(d.get('to_address', '')).strip()
        pickup = str(d.get('pickup_date', '')).strip()
        from_lat = Decimal(str(d.get('from_lat', '0')))
        from_lon = Decimal(str(d.get('from_lon', '0')))
        to_lat = Decimal(str(d.get('to_lat', '0')))
        to_lon = Decimal(str(d.get('to_lon', '0')))

        if not from_address or not to_address or not pickup:
            return JsonResponse({'error': 'From, To, and Pickup Date are required.'}, status=400)

        pickup_date = date.fromisoformat(pickup)
        
        # Package details
        package_type = str(d.get('package_type', 'Standard Parcel')).strip()
        weight_kg = Decimal(str(d.get('weight_kg', '1.0')))
        recipient_name = str(d.get('recipient_name', '')).strip()
        recipient_phone = str(d.get('recipient_phone', '')).strip()

        # Generate unique Product ID: PROD + 8 digits
        while True:
            product_id = 'PROD' + ''.join(random.choices(string.digits, k=8))
            if not Shipment.objects.filter(product_id=product_id).exists():
                break

        # Calculate estimated delivery and pricing based on distance
        import math
        R = 6371  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [float(from_lat), float(from_lon), float(to_lat), float(to_lon)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c

        # Estimated delivery days: min 1 day, ~350km per day
        transit_days = max(1, math.ceil(distance_km / 350))
        estimated_delivery = pickup_date + timedelta(days=transit_days)

        # Base price formula: base ₹150 + ₹0.8/km + ₹50/kg
        calc_price = Decimal(150) + Decimal(str(round(distance_km * 0.8, 2))) + (weight_kg * Decimal(50))

        shipment = Shipment.objects.create(
            user=user,
            product_id=product_id,
            from_address=from_address,
            to_address=to_address,
            from_lat=from_lat,
            from_lon=from_lon,
            to_lat=to_lat,
            to_lon=to_lon,
            pickup_date=pickup_date,
            estimated_delivery=estimated_delivery,
            status='CREATED',
            package_type=package_type,
            weight_kg=weight_kg,
            price=round(calc_price, 2),
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            current_location=from_address
        )

        # Create initial milestone checkpoint
        # Create initial milestone checkpoint
        ShipmentTrackingUpdate.objects.create(
            shipment=shipment,
            status='CREATED',
            location=from_address,
            remarks='Booking confirmed. Awaiting carrier pickup.',
            updated_by=user
        )

        # Send booking confirmation email
        if user.email:
            try:
                send_mail(
                    subject=f'Shipment Booking Confirmed - {shipment.product_id}',
                    message=f"""
Hello {user.get_full_name() or user.username},

Your shipment has been successfully booked with Ashwa Logistics.

Shipment Details
----------------
Tracking ID: {shipment.product_id}
Status: {shipment.status}

From:
{shipment.from_address}

To:
{shipment.to_address}

Package Type:
{shipment.package_type}

Weight:
{shipment.weight_kg} kg

Price:
₹{shipment.price}

Pickup Date:
{shipment.pickup_date}

Estimated Delivery:
{shipment.estimated_delivery}

Recipient:
{shipment.recipient_name}

Recipient Phone:
{shipment.recipient_phone}

Your shipment is now awaiting carrier pickup.

Thank you for choosing Ashwa Logistics.

Regards,
Ashwa Logistics Team
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as email_error:
                print(f"Email sending failed: {email_error}")

        return JsonResponse({
            'message': 'Shipment created successfully!',
            'shipment': serialize_shipment(
                shipment,
                include_history=True
            )
        }, status=201)

    except Exception as e:
        return JsonResponse(
            {'error': f'Failed to create shipment: {str(e)}'},
            status=400
        )

def shipment_detail_api(request, product_id):
    pid = product_id.strip()
    try:
        s = Shipment.objects.prefetch_related('tracking_updates').filter(product_id__iexact=pid).first()
        if not s:
            s = Shipment.objects.prefetch_related('tracking_updates').filter(product_id__icontains=pid).first()
        if not s:
            return JsonResponse({'error': f'No shipment found with Product ID "{pid}". Try e.g. PROD88291043 or PROD77412950.'}, status=404)
        return JsonResponse({'shipment': serialize_shipment(s, include_history=True)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def my_shipments_api(request):
    user = get_authenticated_user(request)
    if not user:
        return JsonResponse({'error': 'Please login first.'}, status=401)
    
    shipments = Shipment.objects.filter(user=user).order_by('-created_at')
    return JsonResponse({
        'shipments': [serialize_shipment(s) for s in shipments]
    })

# ==========================================
# CUSTOMER ENQUIRY & CONTACT APIS
# ==========================================

@csrf_exempt
def enquiry_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    name = str(d.get('name', '')).strip()
    email = str(d.get('email', '')).strip()
    phone = str(d.get('phone', '')).strip()
    comment = str(d.get('comment', '')).strip()

    if not name or not email or not comment:
        return JsonResponse({'error': 'Please fill all required fields.'}, status=400)

    user = get_authenticated_user(request)
    Enquiry.objects.create(
        user=user,
        name=name,
        email=email,
        phone=phone,
        comment=comment,
        status='PENDING'
    )
    return JsonResponse({'message': 'Your enquiry has been received. Our team will contact you shortly!'})

@csrf_exempt
def contact_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    name = str(d.get('name', '')).strip()
    email = str(d.get('email', '')).strip()
    phone = str(d.get('phone', '')).strip()
    message = str(d.get('message', '')).strip()

    if not name or not email or not message:
        return JsonResponse({'error': 'Please fill all required fields.'}, status=400)

    user = get_authenticated_user(request)
    ContactMessage.objects.create(
        user=user,
        name=name,
        email=email,
        phone=phone,
        message=message
    )
    return JsonResponse({'message': 'Thank you! Your message has been sent successfully.'})

# ==========================================
# ADMIN AUTHENTICATION & MANAGEMENT APIS
# ==========================================

@csrf_exempt
def admin_login_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    username = str(d.get('username', '')).strip()
    password = str(d.get('password', ''))

    user = authenticate(request, username=username, password=password)
    if not user:
        # Check if email was provided instead of username
        try:
            matched_user = User.objects.get(email__iexact=username)
            user = authenticate(request, username=matched_user.username, password=password)
        except User.DoesNotExist:
            pass

    if not user or not user.is_staff:
        return JsonResponse({'error': 'Invalid administrator credentials.'}, status=403)

    login(request, user)
    request.session.save()

    return JsonResponse({
        'message': 'Admin login successful',
        'token': request.session.session_key,
        'admin': {'id': user.id, 'username': user.username, 'email': user.email},
        'user': {'id': user.id, 'username': user.username, 'email': user.email, 'is_staff': user.is_staff}
    })

@csrf_exempt
def admin_logout_api(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})

def check_admin(request):
    user = get_authenticated_user(request)
    return bool(user and user.is_active and user.is_staff)

def admin_dashboard_api(request):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    
    status_counts = dict(Shipment.objects.values_list('status').annotate(total=Count('id')))
    total_revenue = Shipment.objects.exclude(status='CANCELLED').aggregate(sum=Sum('price'))['sum'] or Decimal('0.00')

    stats = {
        'users': User.objects.filter(is_staff=False).count(),
        'shipments': Shipment.objects.count(),
        'delivered': status_counts.get('DELIVERED', 0),
        'in_transit': status_counts.get('IN TRANSIT', 0),
        'pending': status_counts.get('PENDING', 0) + status_counts.get('CREATED', 0),
        'cancelled': status_counts.get('CANCELLED', 0),
        'enquiries': Enquiry.objects.count(),
        'pending_enquiries': Enquiry.objects.filter(status='PENDING').count(),
        'messages': ContactMessage.objects.count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'revenue': float(total_revenue),
        'shipment_status': {
            'Created': status_counts.get('CREATED', 0),
            'Pending': status_counts.get('PENDING', 0),
            'In Transit': status_counts.get('IN TRANSIT', 0),
            'Out for Delivery': status_counts.get('OUT FOR DELIVERY', 0),
            'Delivered': status_counts.get('DELIVERED', 0),
            'Cancelled': status_counts.get('CANCELLED', 0),
        }
    }

    recent_shipments = [
        serialize_shipment(s) for s in Shipment.objects.select_related('user').order_by('-created_at')[:8]
    ]
    recent_enquiries = [
        {
            'id': e.id,
            'name': e.name,
            'email': e.email,
            'comment': e.comment,
            'status': e.status,
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M')
        } for e in Enquiry.objects.order_by('-created_at')[:5]
    ]
    recent_messages = [
        {
            'id': m.id,
            'name': m.name,
            'email': m.email,
            'message': m.message,
            'is_read': m.is_read,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        } for m in ContactMessage.objects.order_by('-created_at')[:5]
    ]

    return JsonResponse({
        'stats': stats,
        'recent_shipments': recent_shipments,
        'recent_enquiries': recent_enquiries,
        'recent_messages': recent_messages
    })

def admin_shipments_list_api(request):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().upper()

    qs = Shipment.objects.select_related('user').all()
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(
            Q(product_id__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(from_address__icontains=q) |
            Q(to_address__icontains=q) |
            Q(recipient_name__icontains=q)
        )
    
    shipments = [serialize_shipment(s, include_history=True) for s in qs[:100]]
    return JsonResponse({'shipments': shipments, 'total': qs.count()})

@csrf_exempt
def admin_shipment_update_status_api(request, product_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    new_status = str(d.get('status', '')).strip().upper().replace('_', ' ')
    location = str(d.get('location', '')).strip()
    remarks = str(d.get('remarks', '')).strip()

    valid_statuses = [choice[0] for choice in Shipment.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'error': f'Invalid status. Allowed: {", ".join(valid_statuses)}'}, status=400)

    try:
        shipment = Shipment.objects.get(product_id__iexact=product_id.strip())
    except Shipment.DoesNotExist:
        return JsonResponse({'error': 'Shipment not found.'}, status=404)

    shipment.status = new_status
    if location:
        shipment.current_location = location
    shipment.save()

    # Append checkpoint
    ShipmentTrackingUpdate.objects.create(
        shipment=shipment,
        status=new_status,
        location=location or shipment.current_location or shipment.to_address,
        remarks=remarks or f"Status updated to {new_status} by Admin",
        updated_by=request.user
    )

    return JsonResponse({
        'message': f'Shipment status updated to {new_status}',
        'shipment': serialize_shipment(shipment, include_history=True)
    })

@csrf_exempt
def admin_shipment_delete_api(request, product_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        shipment = Shipment.objects.get(product_id__iexact=product_id.strip())
        shipment.delete()
        return JsonResponse({'message': 'Shipment deleted successfully.'})
    except Shipment.DoesNotExist:
        return JsonResponse({'error': 'Shipment not found.'}, status=404)

def admin_enquiries_list_api(request):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    
    status_filter = request.GET.get('status', '').strip().upper()
    q = request.GET.get('q', '').strip()

    qs = Enquiry.objects.all()
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(comment__icontains=q)
        )
    
    items = [
        {
            'id': e.id,
            'name': e.name,
            'email': e.email,
            'phone': e.phone,
            'comment': e.comment,
            'status': e.status,
            'admin_notes': e.admin_notes,
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M')
        } for e in qs
    ]
    return JsonResponse({'enquiries': items, 'total': qs.count()})

@csrf_exempt
def admin_enquiry_update_status_api(request, enquiry_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    d = get_json_body(request)
    new_status = str(d.get('status', '')).strip().upper()
    admin_notes = str(d.get('admin_notes', '')).strip()

    try:
        enquiry = Enquiry.objects.get(id=enquiry_id)
    except Enquiry.DoesNotExist:
        return JsonResponse({'error': 'Enquiry not found.'}, status=404)

    if new_status:
        enquiry.status = new_status
    if admin_notes:
        enquiry.admin_notes = admin_notes
    enquiry.save()

    return JsonResponse({'message': 'Enquiry status updated successfully.'})

@csrf_exempt
def admin_enquiry_delete_api(request, enquiry_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        Enquiry.objects.get(id=enquiry_id).delete()
        return JsonResponse({'message': 'Enquiry deleted successfully.'})
    except Enquiry.DoesNotExist:
        return JsonResponse({'error': 'Enquiry not found.'}, status=404)

def admin_contact_messages_list_api(request):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    
    read_filter = request.GET.get('read', '').strip().lower()
    q = request.GET.get('q', '').strip()

    qs = ContactMessage.objects.all()
    if read_filter == 'true':
        qs = qs.filter(is_read=True)
    elif read_filter == 'false':
        qs = qs.filter(is_read=False)
    
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(message__icontains=q)
        )
    
    items = [
        {
            'id': m.id,
            'name': m.name,
            'email': m.email,
            'phone': m.phone,
            'message': m.message,
            'is_read': m.is_read,
            'admin_reply': m.admin_reply,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        } for e in qs for m in [e]
    ]
    return JsonResponse({'messages': items, 'total': qs.count()})

@csrf_exempt
def admin_contact_message_toggle_read_api(request, message_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        msg = ContactMessage.objects.get(id=message_id)
        d = get_json_body(request)
        if 'is_read' in d:
            msg.is_read = bool(d['is_read'])
        else:
            msg.is_read = not msg.is_read
        msg.save()
        return JsonResponse({'message': 'Status updated', 'is_read': msg.is_read})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found.'}, status=404)

@csrf_exempt
def admin_contact_message_delete_api(request, message_id):
    if not check_admin(request):
        return JsonResponse({'error': 'Admin authorization required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        ContactMessage.objects.get(id=message_id).delete()
        return JsonResponse({'message': 'Message deleted successfully.'})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found.'}, status=404)

def admin_users_list_api(request):
    """
    Return all non-staff customers for the admin dashboard.
    """

    if not check_admin(request):
        return JsonResponse(
            {
                'error': 'Admin authorization required.'
            },
            status=401
        )

    users = (
        User.objects
        .filter(is_staff=False)
        .annotate(
            shipments_count=Count('shipments')
        )
        .order_by('-date_joined')
    )

    data = []

    for user in users:
        data.append({
            'id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'shipments_count': user.shipments_count,
            'is_active': user.is_active,
            'date_joined': (
                user.date_joined.strftime('%Y-%m-%d')
                if user.date_joined
                else ''
            ),
        })

    return JsonResponse({
        'users': data,
        'total': len(data),
    })
    
def admin_customer_performance_api(request, user_id):
    """
    Return complete performance information for one customer.

    Admin only.
    """

    if not check_admin(request):
        return JsonResponse(
            {'error': 'Admin authorization required.'},
            status=401
        )

    try:
        customer = User.objects.get(
            pk=user_id,
            is_staff=False
        )
    except User.DoesNotExist:
        return JsonResponse(
            {'error': 'Customer not found.'},
            status=404
        )

    shipments = (
        Shipment.objects
        .filter(user=customer)
        .prefetch_related('tracking_updates')
        .order_by('-created_at')
    )

    # =====================================================
    # BASIC COUNTS
    # =====================================================

    total_bookings = shipments.count()

    delivered = 0
    in_transit = 0
    out_for_delivery = 0
    pending = 0
    cancelled = 0

    # =====================================================
    # FINANCIAL / PACKAGE DATA
    # =====================================================

    total_spend = Decimal('0.00')
    total_weight = Decimal('0.00')

    # =====================================================
    # DELIVERY PERFORMANCE
    # =====================================================

    on_time_deliveries = 0
    late_deliveries = 0

    shipment_data = []

    # =====================================================
    # PROCESS SHIPMENTS
    # =====================================================

    for shipment in shipments:

        status = shipment.status

        # -----------------------------
        # STATUS COUNTS
        # -----------------------------

        if status == 'DELIVERED':
            delivered += 1

        elif status == 'IN TRANSIT':
            in_transit += 1

        elif status == 'OUT FOR DELIVERY':
            out_for_delivery += 1

        elif status in ['CREATED', 'PENDING']:
            pending += 1

        elif status == 'CANCELLED':
            cancelled += 1

        # -----------------------------
        # SPENDING / WEIGHT
        # -----------------------------

        if status != 'CANCELLED':

            if shipment.price is not None:
                total_spend += shipment.price

            if shipment.weight_kg is not None:
                total_weight += shipment.weight_kg

        # -----------------------------
        # ON-TIME DELIVERY
        # -----------------------------

        on_time = None

        if status == 'DELIVERED':

            delivered_update = None

            tracking_updates = list(
                shipment.tracking_updates.all()
            )

            # Latest tracking update first
            tracking_updates.sort(
                key=lambda x: x.timestamp,
                reverse=True
            )

            # Find latest DELIVERED event
            for update in tracking_updates:

                if update.status == 'DELIVERED':
                    delivered_update = update
                    break

            if delivered_update:

                delivery_date = timezone.localtime(
                    delivered_update.timestamp
                ).date()

                expected_date = shipment.estimated_delivery

                if expected_date:

                    if delivery_date <= expected_date:

                        on_time = True
                        on_time_deliveries += 1

                    else:

                        on_time = False
                        late_deliveries += 1

        # =================================================
        # SHIPMENT DATA FOR FRONTEND
        # =================================================

        shipment_data.append({

            'id': shipment.id,

            'product_id': shipment.product_id,

            'status': shipment.status,

            'from_address': shipment.from_address,

            'to_address': shipment.to_address,

            'package_type': shipment.package_type,

            'weight_kg': (
                float(shipment.weight_kg)
                if shipment.weight_kg is not None
                else 0
            ),

            'price': (
                float(shipment.price)
                if shipment.price is not None
                else 0
            ),

            'pickup_date': (
                shipment.pickup_date.strftime('%Y-%m-%d')
                if shipment.pickup_date
                else ''
            ),

            'estimated_delivery': (
                shipment.estimated_delivery.strftime('%Y-%m-%d')
                if shipment.estimated_delivery
                else ''
            ),

            'current_location': (
                shipment.current_location or ''
            ),

            'recipient_name': (
                shipment.recipient_name or ''
            ),

            'recipient_phone': (
                shipment.recipient_phone or ''
            ),

            'on_time': on_time,

            'created_at': (
                timezone.localtime(
                    shipment.created_at
                ).strftime('%Y-%m-%d %H:%M')
                if shipment.created_at
                else ''
            ),

            'updated_at': (
                timezone.localtime(
                    shipment.updated_at
                ).strftime('%Y-%m-%d %H:%M')
                if shipment.updated_at
                else ''
            ),
        })

    # =====================================================
    # CALCULATE PERFORMANCE
    # =====================================================

    non_cancelled_bookings = (
        total_bookings - cancelled
    )

    # Average order value
    if non_cancelled_bookings > 0:

        average_order_value = (
            total_spend /
            Decimal(non_cancelled_bookings)
        )

    else:

        average_order_value = Decimal('0.00')

    # Delivery rate
    if total_bookings > 0:

        delivery_rate = (
            delivered /
            total_bookings
        ) * 100

    else:

        delivery_rate = Decimal('0.00')

    # On-time delivery rate
    if delivered > 0:

        on_time_rate = (
            on_time_deliveries /
            delivered
        ) * 100

    else:

        on_time_rate = Decimal('0.00')

    # =====================================================
    # RETURN RESPONSE
    # =====================================================

    return JsonResponse({

        'customer': {

            'id': customer.id,

            'username': customer.username,

            'name': (
                customer.get_full_name()
                or customer.username
            ),

            'email': customer.email,

            'is_active': customer.is_active,

            'date_joined': (
                customer.date_joined.strftime('%Y-%m-%d')
                if customer.date_joined
                else ''
            ),
        },

        'performance': {

            'total_bookings': total_bookings,

            'delivered': delivered,

            'in_transit': in_transit,

            'out_for_delivery': out_for_delivery,

            'pending': pending,

            'cancelled': cancelled,

            'total_spend': float(
                total_spend
            ),

            'average_order_value': float(
                average_order_value
            ),

            'total_weight': float(
                total_weight
            ),

            'delivery_rate': round(
                float(delivery_rate),
                2
            ),

            'on_time_deliveries': (
                on_time_deliveries
            ),

            'late_deliveries': (
                late_deliveries
            ),

            'on_time_rate': round(
                float(on_time_rate),
                2
            ),
        },

        'shipments': shipment_data,
    })
@csrf_exempt
def admin_user_toggle_active_api(request, user_id):
    """
    Activate or deactivate a customer account.
    Staff accounts cannot be changed through this endpoint.
    """

    if not check_admin(request):
        return JsonResponse(
            {
                'error': 'Admin authorization required.'
            },
            status=401
        )

    try:
        user = User.objects.get(
            pk=user_id,
            is_staff=False
        )

    except User.DoesNotExist:
        return JsonResponse(
            {
                'error': 'Customer not found.'
            },
            status=404
        )

    user.is_active = not user.is_active

    user.save(
        update_fields=['is_active']
    )

    return JsonResponse({

        'success': True,

        'user': {
            'id': user.id,
            'is_active': user.is_active,
        },

        'message': (
            'Customer activated successfully.'
            if user.is_active
            else 'Customer disabled successfully.'
        ),
    })
# ==========================================
# ADMIN CUSTOMER PERFORMANCE API
# ==========================================

def admin_customer_performance_api(request, user_id):
    """
    Return complete performance statistics for one customer.
    Admin/staff only.
    """

    if not check_admin(request):
        return JsonResponse(
            {'error': 'Admin authorization required.'},
            status=401
        )

    try:
        customer = User.objects.get(
            id=user_id,
            is_staff=False
        )
    except User.DoesNotExist:
        return JsonResponse(
            {'error': 'Customer not found.'},
            status=404
        )

    shipments = Shipment.objects.filter(
        user=customer
    ).prefetch_related(
        'tracking_updates'
    )

    total_bookings = shipments.count()

    delivered = shipments.filter(
        status='DELIVERED'
    ).count()

    in_transit = shipments.filter(
        status='IN TRANSIT'
    ).count()

    out_for_delivery = shipments.filter(
        status='OUT FOR DELIVERY'
    ).count()

    pending = shipments.filter(
        status__in=['CREATED', 'PENDING']
    ).count()

    cancelled = shipments.filter(
        status='CANCELLED'
    ).count()

    total_spend = shipments.exclude(
        status='CANCELLED'
    ).aggregate(
        total=Sum('price')
    )['total'] or Decimal('0.00')

    average_order_value = (
        total_spend / delivered
        if delivered > 0
        else Decimal('0.00')
    )

    # ------------------------------------------
    # DELIVERY PERFORMANCE
    # ------------------------------------------

    on_time_deliveries = 0
    late_deliveries = 0

    shipment_data = []

    for shipment in shipments:

        delivered_update = None

        for update in shipment.tracking_updates.all():
            if update.status == 'DELIVERED':
                delivered_update = update
                break

        on_time = None

        if delivered_update:
            delivered_date = delivered_update.timestamp.date()

            if delivered_date <= shipment.estimated_delivery:
                on_time = True
                on_time_deliveries += 1
            else:
                on_time = False
                late_deliveries += 1

        shipment_data.append({
            'product_id': shipment.product_id,
            'status': shipment.status,
            'from_address': shipment.from_address,
            'to_address': shipment.to_address,
            'package_type': shipment.package_type,
            'weight_kg': float(shipment.weight_kg),
            'price': float(shipment.price),
            'pickup_date': shipment.pickup_date.isoformat(),
            'estimated_delivery': shipment.estimated_delivery.isoformat(),
            'current_location': shipment.current_location,
            'on_time': on_time,
            'created_at': shipment.created_at.strftime(
                '%Y-%m-%d %H:%M'
            ),
        })

    delivery_rate = (
        (delivered / total_bookings) * 100
        if total_bookings > 0
        else 0
    )

    on_time_rate = (
        (on_time_deliveries / delivered) * 100
        if delivered > 0
        else 0
    )

    return JsonResponse({
        'customer': {
            'id': customer.id,
            'name': customer.get_full_name() or customer.username,
            'email': customer.email,
            'username': customer.username,
            'is_active': customer.is_active,
            'date_joined': customer.date_joined.strftime('%Y-%m-%d'),
        },

        'performance': {
            'total_bookings': total_bookings,
            'delivered': delivered,
            'in_transit': in_transit,
            'out_for_delivery': out_for_delivery,
            'pending': pending,
            'cancelled': cancelled,

            'total_spend': float(total_spend),
            'average_order_value': float(average_order_value),

            'delivery_rate': round(delivery_rate, 2),
            'on_time_deliveries': on_time_deliveries,
            'late_deliveries': late_deliveries,
            'on_time_rate': round(on_time_rate, 2),
        },

        'shipments': shipment_data
    })