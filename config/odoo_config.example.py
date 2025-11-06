"""Odoo configuration example. Copy to odoo_config.py and fill in your credentials."""

ODOO_CONFIG = {
    'login_url': 'http://localhost:8069',
    'po_list_url': 'http://localhost:8069/odoo/purchase-orders',
    'credentials': {
        'email': 'your.email@example.com',
        'password': 'YOUR_PASSWORD_HERE'
    },
    'workers': 8
}
