from django.contrib import admin
from .models import Shipment, ShipmentTrackingUpdate, Enquiry, ContactMessage

# Django Admin Customization
admin.site.site_header = "Ashwa Logistics — Django Backend Administration"
admin.site.site_title = "Ashwa Logistics Admin"
admin.site.index_title = "Django Backend Database & Operations"
admin.site.site_url = "http://127.0.0.1:5500/"

class ShipmentTrackingUpdateInline(admin.TabularInline):
    model = ShipmentTrackingUpdate
    extra = 1
    readonly_fields = ('timestamp',)

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'product_id', 'user', 'status', 'from_address', 'to_address', 
        'package_type', 'price', 'pickup_date', 'estimated_delivery', 'created_at'
    )
    list_filter = ('status', 'package_type', 'pickup_date', 'created_at')
    search_fields = ('product_id', 'user__username', 'user__email', 'from_address', 'to_address', 'recipient_name')
    list_editable = ('status',)
    inlines = [ShipmentTrackingUpdateInline]
    date_hierarchy = 'created_at'

@admin.register(ShipmentTrackingUpdate)
class ShipmentTrackingUpdateAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'timestamp', 'updated_by')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__product_id', 'location', 'remarks')

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'comment', 'admin_notes')
    list_editable = ('status',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'message', 'admin_reply')
    list_editable = ('is_read',)
