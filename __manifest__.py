{
    'name': 'Sales Customization',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Custom Fields for Product Template',
    'description': 'This module adds custom fields to the Product Template (Item Master).',
    'author':'Mohtashim',
    'depends': ['base', 'product', 'sale_management', 'web'], 
    'data': [
        'views/product_template_view.xml',
        'views/packaging_details.xml',
        'views/sale_order_line.xml',
        'views/menu.xml',
        "report/report_action.xml",
        "report/sales_order_template.xml",
        "security/ir.model.access.csv",
        "views/hs_code.xml",
        "report/performa_invoice.xml",
        "report/order_sheet.xml"
        # "report/report.xml"
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
