{
    'name': 'Distributor Order Management',
    'version': '1.0.0',
    'category': 'Sales/Distributor',
    'summary': 'Manage distributor orders with salesperson approval workflow that converts to Odoo Sale Orders.',
    'description': '''
Distributor Order Management
=============================
Key Features:
- Mark partners as Distributors and assign a dedicated Salesperson
- Distributors create orders (Draft → Submitted)
- Assigned Salesperson reviews, approves or rejects each order
- On approval the Distributor Order is automatically converted into a confirmed Sale Order
- Full traceability: distributor order links back to the generated sale order
    ''',
    'author': 'Alpha Edge Solutions',
    'company': 'Alpha Edge Solutions',
    'maintainer': 'Alpha Edge Solutions',
    'website': 'https://alphaedgesolution.com',
    'depends': ['base', 'sale_management', 'product', 'uom', 'mrp'],
    'data': [
        # security – load first
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # data
        'data/sequence.xml',
        # views
        'views/res_partner_views.xml',
        'views/distributor_order_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
