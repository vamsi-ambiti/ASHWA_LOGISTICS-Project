from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from logistics import views


urlpatterns = [

    # ========================================================
    # CUSTOMER & PUBLIC PAGES
    # ========================================================

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'login/',
        views.login_page,
        name='login_page'
    ),

    path(
        'signup/',
        views.signup_page,
        name='signup_page'
    ),

    path(
        'enquiry/',
        views.enquiry_page,
        name='enquiry_page'
    ),

    path(
        'contact/',
        views.contact_page,
        name='contact_page'
    ),


    # ========================================================
    # ADMIN / DASHBOARD PAGES
    # ========================================================

    path(
        'admin/login/',
        views.admin_login_page,
        name='admin_login_page'
    ),

    path(
        'admin/dashboard/',
        views.admin_dashboard_page,
        name='admin_dashboard_page'
    ),

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        'django-admin/',
        lambda req: redirect('/admin/', permanent=False)
    ),


    # ========================================================
    # CUSTOMER / GENERAL APIs
    # ========================================================

    path(
        'api/',
        views.api_index,
        name='api_index'
    ),

    path(
        'api/csrf/',
        views.csrf_api,
        name='api_csrf'
    ),

    path(
        'api/me/',
        views.me_api,
        name='api_me'
    ),

    path(
        'api/signup/',
        views.signup_api,
        name='api_signup'
    ),

    path(
        'api/login/',
        views.login_api,
        name='api_login'
    ),

    path(
        'api/logout/',
        views.logout_api,
        name='api_logout'
    ),

    path(
        'api/shipments/',
        views.shipment_create_api,
        name='api_shipment_create'
    ),

    path(
        'api/shipments/<str:product_id>/',
        views.shipment_detail_api,
        name='api_shipment_detail'
    ),

    path(
        'api/my-shipments/',
        views.my_shipments_api,
        name='api_my_shipments'
    ),

    path(
        'api/enquiries/',
        views.enquiry_api,
        name='api_enquiry'
    ),

    path(
        'api/contact/',
        views.contact_api,
        name='api_contact'
    ),


    # ========================================================
    # ADMIN APIs
    # ========================================================

    path(
        'api/admin/login/',
        views.admin_login_api,
        name='api_admin_login'
    ),

    path(
        'api/admin/logout/',
        views.admin_logout_api,
        name='api_admin_logout'
    ),

    path(
        'api/admin/dashboard/',
        views.admin_dashboard_api,
        name='api_admin_dashboard'
    ),

    # --------------------------------------------------------
    # SHIPMENTS
    # --------------------------------------------------------

    path(
        'api/admin/shipments/',
        views.admin_shipments_list_api,
        name='api_admin_shipments_list'
    ),

    path(
        'api/admin/shipments/<str:product_id>/status/',
        views.admin_shipment_update_status_api,
        name='api_admin_shipment_status'
    ),

    path(
        'api/admin/shipments/<str:product_id>/delete/',
        views.admin_shipment_delete_api,
        name='api_admin_shipment_delete'
    ),


    # --------------------------------------------------------
    # ENQUIRIES
    # --------------------------------------------------------

    path(
        'api/admin/enquiries/',
        views.admin_enquiries_list_api,
        name='api_admin_enquiries_list'
    ),

    path(
        'api/admin/enquiries/<int:enquiry_id>/status/',
        views.admin_enquiry_update_status_api,
        name='api_admin_enquiry_status'
    ),

    path(
        'api/admin/enquiries/<int:enquiry_id>/delete/',
        views.admin_enquiry_delete_api,
        name='api_admin_enquiry_delete'
    ),


    # --------------------------------------------------------
    # CONTACT MESSAGES
    # --------------------------------------------------------

    path(
        'api/admin/contact-messages/',
        views.admin_contact_messages_list_api,
        name='api_admin_contact_messages_list'
    ),

    path(
        'api/admin/contact-messages/<int:message_id>/mark-read/',
        views.admin_contact_message_toggle_read_api,
        name='api_admin_contact_message_toggle_read'
    ),

    path(
        'api/admin/contact-messages/<int:message_id>/delete/',
        views.admin_contact_message_delete_api,
        name='api_admin_contact_message_delete'
    ),


    # --------------------------------------------------------
    # CUSTOMERS
    # --------------------------------------------------------

    path(
        'api/admin/users/',
        views.admin_users_list_api,
        name='api_admin_users_list'
    ),

    # CUSTOMER PERFORMANCE
    path(
        'api/admin/users/<int:user_id>/performance/',
        views.admin_customer_performance_api,
        name='api_admin_customer_performance'
    ),

    # ACTIVATE / DEACTIVATE CUSTOMER
    path(
        'api/admin/users/<int:user_id>/toggle-active/',
        views.admin_user_toggle_active_api,
        name='api_admin_user_toggle_active'
    ),

]