CREATE DATABASE IF NOT EXISTS ashwa_logistics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ashwa_logistics;

SHOW TABLES;

SELECT id, username, email, is_staff, is_active
FROM auth_user
WHERE is_staff = 0
ORDER BY id DESC;

SELECT id, username, email, is_staff, is_superuser, is_active
FROM auth_user
ORDER BY id DESC;


SELECT id, username, email, is_staff, is_superuser, is_active
FROM auth_user;

SELECT id, username, email, is_staff, is_active
FROM auth_user
WHERE is_staff = 0;


SELECT id, username, email, is_staff, is_active
FROM auth_user
WHERE is_staff = 0;

DESCRIBE logistics_shipment;

SELECT id, username, email
FROM auth_user
WHERE username = 'customer1';


 

INSERT INTO logistics_shipment (
    product_id,
    from_address,
    to_address,
    from_lat,
    from_lon,
    to_lat,
    to_lon,
    pickup_date,
    estimated_delivery,
    status,
    created_at,
    updated_at,
    user_id,
    current_location,
    package_type,
    price,
    recipient_name,
    recipient_phone,
    weight_kg
)
VALUES (
    'TEST-001',
    'Tirupati, Andhra Pradesh',
    'Bengaluru, Karnataka',
    13.6288,
    79.4192,
    12.9716,
    77.5946,
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 3 DAY),
    'IN TRANSIT',
    NOW(6),
    NOW(6),
    2,
    'Tirupati Hub',
    'Box',
    850.00,
    'Test Recipient',
    '9000000000',
    5.50
);

SELECT
    id,
    product_id,
    user_id,
    status,
    price,
    weight_kg
FROM logistics_shipment
WHERE user_id = 2;




INSERT INTO logistics_shipment (
    product_id, from_address, to_address,
    from_lat, from_lon, to_lat, to_lon,
    pickup_date, estimated_delivery, status,
    created_at, updated_at, user_id,
    current_location, package_type, price,
    recipient_name, recipient_phone, weight_kg
)
VALUES
(
    'TEST-002',
    'Chennai, Tamil Nadu',
    'Tirupati, Andhra Pradesh',
    13.0827, 80.2707,
    13.6288, 79.4192,
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 2 DAY),
    'DELIVERED',
    NOW(6), NOW(6), 2,
    'Tirupati',
    'Box', 1200.00,
    'Test Recipient 2', '9000000001', 8.00
),
(
    'TEST-003',
    'Hyderabad, Telangana',
    'Tirupati, Andhra Pradesh',
    17.3850, 78.4867,
    13.6288, 79.4192,
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 4 DAY),
    'OUT FOR DELIVERY',
    NOW(6), NOW(6), 2,
    'Tirupati Delivery Hub',
    'Parcel', 650.00,
    'Test Recipient 3', '9000000002', 3.00
),
(
    'TEST-004',
    'Bengaluru, Karnataka',
    'Tirupati, Andhra Pradesh',
    12.9716, 77.5946,
    13.6288, 79.4192,
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 5 DAY),
    'CANCELLED',
    NOW(6), NOW(6), 2,
    'Bengaluru',
    'Box', 500.00,
    'Test Recipient 4', '9000000003', 2.50
);


SELECT
    product_id,
    status,
    price,
    weight_kg
FROM logistics_shipment
WHERE user_id = 2
ORDER BY id;


SELECT
    id,
    username,
    email,
    is_staff,
    is_active
FROM auth_user
WHERE is_staff = 0
ORDER BY id;


SELECT
    u.id AS customer_id,
    u.username,
    COUNT(s.id) AS total_bookings,
    COALESCE(SUM(
        CASE
            WHEN s.status <> 'CANCELLED'
            THEN s.price
            ELSE 0
        END
    ), 0) AS total_spend,
    COALESCE(SUM(
        CASE
            WHEN s.status <> 'CANCELLED'
            THEN s.weight_kg
            ELSE 0
        END
    ), 0) AS total_weight,
    SUM(CASE WHEN s.status = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered,
    SUM(CASE WHEN s.status = 'IN TRANSIT' THEN 1 ELSE 0 END) AS in_transit,
    SUM(CASE WHEN s.status = 'OUT FOR DELIVERY' THEN 1 ELSE 0 END) AS out_for_delivery,
    SUM(CASE WHEN s.status IN ('CREATED', 'PENDING') THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN s.status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled
FROM auth_user u
LEFT JOIN logistics_shipment s
    ON s.user_id = u.id
WHERE u.is_staff = 0
GROUP BY u.id, u.username
ORDER BY u.id;


SELECT id, product_id, user_id, status
FROM logistics_shipment
WHERE product_id IN (
    'TEST-001',
    'TEST-002',
    'TEST-003',
    'TEST-004'
);

SELECT id, product_id, user_id, status
FROM logistics_shipment
WHERE product_id LIKE 'TEST-%';

SET SQL_SAFE_UPDATES = 0;

DELETE FROM logistics_shipmenttrackingupdate
WHERE shipment_id IN (
    SELECT id
    FROM logistics_shipment
    WHERE product_id IN ('TEST-001', 'TEST-002', 'TEST-003', 'TEST-004')
);

DELETE FROM logistics_shipment
WHERE product_id IN ('TEST-001', 'TEST-002', 'TEST-003', 'TEST-004');

SET SQL_SAFE_UPDATES = 1;

SELECT id, product_id, user_id, status
FROM logistics_shipment
WHERE product_id IN ('TEST-001', 'TEST-002', 'TEST-003', 'TEST-004');

SELECT id, username, email, is_staff, is_active, date_joined
FROM auth_user
ORDER BY id;


SELECT id, product_id, user_id, status, price, weight_kg
FROM logistics_shipment
ORDER BY id;

SELECT id, username, email, is_staff, is_active
FROM auth_user
WHERE username = 'customer1';