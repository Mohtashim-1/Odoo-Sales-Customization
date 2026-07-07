{
    'name': 'Sales Customization',
    'version': '2.2.4',
    'category': 'Sales',
    'summary': 'Extend and enhance the Sales workflow by adding custom fields to the Product Template and Sales Orders for better data capture and reporting.',
    'description': '''
    The Sales Customization module enhances Odoo's standard Sales and Product features by introducing a set of custom fields and views tailored for specialized sales processes. It adds new fields to the Product Template (Item Master) and Sales Orders, allowing for better data control, document generation, and workflow optimization.

    Key Features:
    - Custom fields for Product Template, Sales Orders, and Partners
    - Extended views for sales-related documents
    - Custom Kanban view enhancements for Product Templates
    - Tailored sales reports: Proforma Invoice, Commercial Invoice, Order Sheet, Packaging List, Export Order, BL Instruction, Financial Report, and more
    - User access control through defined security groups
    ''',
    'author':'Mohtashim Shoaib',
    'company': 'Alpha Edge Solutions',
    'maintainer': 'Alpha Edge Solutions',
    'website': 'https://alphaedgesolution.com',
    'assets': {
        'web.assets_backend': [
            'sales_customization/static/lib/apexcharts/apexcharts.min.js',
            'sales_customization/static/src/js/sales_dashboard.js',
            'sales_customization/static/src/xml/sales_dashboard.xml',
            'sales_customization/static/src/scss/sales_dashboard.scss',
        ],
    },
    'depends': ['base', 'product', 'sale_management', 'web', 'crm', 'account', 'project'],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
    # security - Load first
    'security/group.xml',
    'security/ir.model.access.csv',
    'security/record_rules.xml',
    'security/override_rules.xml',
    'security/partner_only_own_contact_rule.xml',
    
    # view
    'views/res_users_views.xml',
    'views/product_category_tag_views.xml',
    'views/product_template_view.xml',
    'views/partner.xml',
    'views/partner_sales_dashboard.xml',
    'views/sale_order.xml',
    'views/project_task_views.xml',
    'views/bank_detail.xml',
    'views/packaging_details.xml',
    "views/shipping_terms.xml",
    "views/hs_code.xml",
    "views/company.xml",
    "views/sale_order_custom_view.xml",
    "views/product_kanban_inherit_view.xml",
    "views/crm_lead_kanban_view.xml",
    "views/crm_lead_search_view.xml",
    "views/crm_lead_form_old_sale.xml",
    "wizard/old_sales_export_wizard_views.xml",
    "views/old_sales_report.xml",
    'views/sale_order_line.xml',
    'views/sale_order_customer_rule.xml',
    'views/sales_dashboard_menu.xml',
    
    # report
    "report/report_action.xml",
    "report/sales_order_template.xml",
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
    'post_init_hook': 'post_init_hook',
}
