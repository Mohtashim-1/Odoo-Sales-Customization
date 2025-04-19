{
    'name': 'Sales Customization',
    'version': '2.0.0',
    'category': 'Sales',
    'summary': 'Custom Fields for Product Template',
    'description': 'This module adds custom fields to the Product Template (Item Master).',
    'author':'Mohtashim',
    # 'assets': {
    # 'web.assets_backend': [
    #     'sales_customization/static/src/css/hide_buttons.css',
    #     'sales_customization/static/src/js/hide_buttons.js',
    #     ],
    # },
    'depends': ['base', 'product', 'sale_management', 'web'], 
    'data': [
    # view
    'views/product_template_view.xml',
    'views/partner.xml',
    'views/sale_order.xml',
    'views/bank_detail.xml',
    'views/packaging_details.xml',
    "views/shipping_terms.xml",
    "views/hs_code.xml",
    "views/company.xml",
    "views/sale_order_custom_view.xml",
    "views/product_kanban_inherit_view.xml",
    'views/sale_order_line.xml',
    # report
    "report/report_action.xml",
    "report/sales_order_template.xml",
    # security
    "security/ir.model.access.csv",
    'security/group.xml',
    # 'security/record_rules.xml',
    # 'security/sale_order_line_access.xml',
    # report
    "report/performa_invoice.xml",
    "report/order_sheet.xml",
    'report/commercial_invoice.xml',
    'report/packaging_list.xml',
    'report/pi.xml',
    'report/financial_report.xml',
    'report/export_order.xml',
    'report/bl_instruction.xml',
    'report/custom_invoice.xml',
    # view
    'views/menu.xml',
],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
