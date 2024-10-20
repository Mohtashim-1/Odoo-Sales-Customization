{
    'name': 'Sales Customization',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Custom Fields for Product Template',
    'description': 'This module adds custom fields to the Product Template (Item Master).',
    'depends': ['base', 'product'],  # Depends on the 'product' module
    'data': [
        'views/product_template_view.xml',
        'views/packaging_details.xml',
        'views/menu.xml'
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}
