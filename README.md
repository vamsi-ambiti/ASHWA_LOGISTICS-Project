# ASHWA_LOGISTICS-Project

Ashwa Logistics is a production-ready, full-stack logistics and shipment tracking web platform built with **Django**, **SQLite / MySQL**, and responsive **HTML5 / CSS3 / JavaScript (Leaflet & Chart.js)**.

---

## 🌟 Key Features

### 🚚 Customer Portal
- **Hero & Fleet Showcase**: Video hero banner with smooth scroll navigation to fleet information and booking sections.
- **Shipment Booking**: Geocoded location autocomplete via OpenStreetMap (Nominatim), automated distance calculation, transit time estimation, and transparent pricing.
- **Live Interactive Tracking**: Real-time Leaflet map displaying route polylines and start/destination markers, along with chronological checkpoint milestones (e.g. Booking Confirmed ➔ Sorting Hub ➔ In Transit ➔ Out for Delivery ➔ Delivered).
- **Customer Account Management**: User registration, session-based authentication, and a **"My Bookings"** drawer allowing customers to track all their past and active packages in one click.
- **Customer Support**: Public **Customer Issue / Enquiry Report** and **Contact Us** forms connected directly to the backend database.

### 🛡️ Admin Operations Suite (`/admin/login/` & `/admin/dashboard/`)
- **Executive Overview**: Real-time KPI summary (Total Shipments, Delivered, In Transit, Pending, Revenue in ₹, Active Users, Unresolved Issues, Unread Messages) plus live **Doughnut** and **Bar** analytics charts powered by Chart.js.
- **Shipments Manager**:
  - Live search by Product ID, customer name, email, origin, or destination.
  - Filter shipments by status (`CREATED`, `PENDING`, `IN TRANSIT`, `OUT FOR DELIVERY`, `DELIVERED`, `CANCELLED`).
  - **Update Status & Checkpoint Modal**: Change delivery status, record the current facility location, and append tracking notes that instantly appear on the customer's tracking timeline.
  - **Tracking History Modal**: View the complete audit trail of checkpoints for any shipment.
  - Safe deletion of shipments.
- **Customer Issues & Enquiries Manager**:
  - Filter by resolution status (`PENDING`, `IN_PROGRESS`, `RESOLVED`).
  - Add administrative resolution notes and mark issues resolved.
- **Contact Inbox**:
  - Search and filter by Read / Unread status.
  - Instant toggle read status and message deletion.
- **Customer Directory**:
  - View registered customers, account creation dates, total bookings count, and toggle account activation.
- **Built-in Django Admin**: Full administrative data control available at `/django-admin/`.

---

## 📂 Project Structure

```text
ASHWA_LOGISTICS/
├── manage.py                     # Root CLI runner (delegates to backend)
├── CONFIGURATION/
│   ├── requirements.txt          # Python dependencies
│   └── .env.example              # Sample environment variables
├── SETUP/
│   ├── README.md                 # Project documentation
│   ├── setup_windows.bat         # Automated Windows setup script
│   └── setup_linux.sh            # Automated Linux setup script
├── backend/
│   ├── manage.py                 # Django management runner
│   ├── seed_data.py              # Database seeding script (Admin & demo data)
│   ├── test_all_endpoints.py     # Automated API & template verification suite
│   ├── ashwa/
│   │   ├── settings.py           # Django settings (Auto-detects DB, resolves frontend)
│   │   ├── urls.py               # Complete page routes & REST API endpoints
│   │   ├── wsgi.py               # WSGI application entry
│   │   └── asgi.py               # ASGI application entry
│   └── logistics/
│       ├── models.py             # Shipment, TrackingMilestone, Enquiry, ContactMessage
│       ├── views.py              # Customer & Admin REST APIs
│       ├── admin.py              # ModelAdmin registrations & inlines
│       └── migrations/           # Database migration files
├── database/
│   └── schema.sql                # Optional MySQL initialization script
└── frontend/
    ├── templates/
    │   ├── index.html            # Public homepage, booking & live tracking
    │   ├── login.html            # Customer sign in
    │   ├── signup.html           # Customer registration
    │   ├── enquiry.html          # Issue report form
    │   ├── contact.html          # Contact us form
    │   ├── admin_login.html      # Secure admin login
    │   └── admin_dashboard.html  # Full administrative suite & operations
    └── static/
        ├── css/
        │   └── admin.css         # Admin portal styles, badges, and modals
        ├── js/
        │   └── app.js            # CSRF helpers, API client, and auth state
        └── background/           # Videos and branding assets
```

---

## ⚡ Quick Start

### 1. Run Migrations
From the project root:
```powershell
python manage.py migrate
```

### 2. Seed Admin and Demo Data
Pre-populates the admin superuser, demo customers, and realistic shipments across India:
```powershell
python backend/seed_data.py
```

### 3. Start Development Server
```powershell
python manage.py runserver
```
The server will start at: `http://127.0.0.1:8000/`

---

## 🔑 Default Credentials

### Operations Administrator
- **Login URL**: `http://127.0.0.1:8000/admin/login/` (or `/django-admin/`)
- **Username**: `admin`
- **Password**: `admin123`

### Demo Customers
- **Login URL**: `http://127.0.0.1:8000/login/`
- **Email**: `rahul@example.com` | **Password**: `customer123`
- **Email**: `priya@example.com` | **Password**: `customer123`
- **Email**: `arun@example.com`  | **Password**: `customer123`

### Sample Tracking Numbers (Ready to Track)
- `PROD88291043` — Status: **DELIVERED** (Mumbai ➔ New Delhi, 5 checkpoints)
- `PROD77412950` — Status: **IN TRANSIT** (Bengaluru ➔ Hyderabad)
- `PROD55109342` — Status: **CREATED** (Chennai ➔ Kolkata)

---

## 🗄️ Database Configuration (Dual-Mode)

The application includes an **intelligent database detector**:
1. **SQLite (Default Zero-Config)**: Operates out of the box with zero external server dependencies, saving to `backend/db.sqlite3`.
2. **MySQL (Optional Production)**: If MySQL is running and configured, create a `.env` file from `CONFIGURATION/.env.example`:
```ini
DB_ENGINE=django.db.backends.mysql
DB_NAME=ashwa_logistics
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```
If the MySQL connection cannot be established, the system automatically falls back to SQLite with an informative notice, ensuring the server never crashes.

---

## 🧪 Automated Testing & Verification

To run the complete verification suite checking all 24 page views and API endpoints:
```powershell
python backend/test_all_endpoints.py
```
Expected output:
```text
==========================================
VERIFICATION SUMMARY: 26 PASSED, 0 FAILED
==========================================
```

