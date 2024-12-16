{
    'name': 'Sales Customization',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Custom Fields for Product Template',
    'description': 'This module adds custom fields to the Product Template (Item Master).',
    'author':'Mohtashim',
    'depends': ['base', 'product', 'sale_management', 'web'], 
    'data': [
    # 'views/sale_order.xml',
    
    'views/product_template_view.xml',
    'views/sale_order.xml',
    'views/bank_detail.xml',
    'views/packaging_details.xml',
    "views/shipping_terms.xml",
    "views/hs_code.xml",
    "views/company.xml",
    # "views/res_partner_view.xml",
    
    # "report/custom_header.xml",

   
    'views/sale_order_line.xml',
    
    
    "report/report_action.xml",
    "report/sales_order_template.xml",
    "security/ir.model.access.csv",
    
    "report/performa_invoice.xml",
    "report/order_sheet.xml",
    'report/commercial_invoice.xml',
    'report/packaging_list.xml',
    'report/financial_report.xml',
    'report/export_order.xml',
    'report/bl_instruction.xml',
    'report/custom_invoice.xml',
    'views/menu.xml',
    # "report/report.xml"
],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
