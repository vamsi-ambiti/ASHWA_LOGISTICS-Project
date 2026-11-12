from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('PENDING', 'Pending'),
        ('IN TRANSIT', 'In Transit'),
        ('OUT FOR DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PACKAGE_CHOICES = [
        ('Standard Parcel', 'Standard Parcel'),
        ('Express Document', 'Express Document'),
        ('Fragile Cargo', 'Fragile Cargo'),
        ('Heavy Freight', 'Heavy Freight'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipments')
    product_id = models.CharField(max_length=30, unique=True, db_index=True)
    from_address = models.CharField(max_length=500)
    to_address = models.CharField(max_length=500)
    from_lat = models.DecimalField(max_digits=9, decimal_places=6)
    from_lon = models.DecimalField(max_digits=9, decimal_places=6)
    to_lat = models.DecimalField(max_digits=9, decimal_places=6)
    to_lon = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_date = models.DateField()
    estimated_delivery = models.DateField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='CREATED', db_index=True)
    
    # Package details
    package_type = models.CharField(max_length=50, choices=PACKAGE_CHOICES, default='Standard Parcel')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=250.00)
    recipient_name = models.CharField(max_length=150, blank=True, default='')
    recipient_phone = models.CharField(max_length=25, blank=True, default='')
    current_location = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product_id} ({self.status})"


class ShipmentTrackingUpdate(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=25)
    location = models.CharField(max_length=255)
    remarks = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.product_id} - {self.status} at {self.location}"


class Enquiry(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=25, blank=True, default='')
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    admin_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Enquiries'

    def __str__(self):
        return f"Enquiry #{self.id} from {self.name} ({self.status})"


class ContactMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=25, blank=True, default='')
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    admin_reply = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message #{self.id} from {self.name} ({'Read' if self.is_read else 'Unread'})"
