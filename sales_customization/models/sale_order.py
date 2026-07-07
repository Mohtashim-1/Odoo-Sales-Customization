from odoo import fields, models, api
from num2words import num2words
from datetime import datetime
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

# from odoo.addons.base.models.res_currency import amount_to_text


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vat = fields.Char(string="Customer VAT", related='partner_id.vat', readonly=True)

    address = fields.Char(string="Address", related='partner_id.vat', readonly=True)
    

    bank_detail_id = fields.Many2one(
    'bank.detail',
    string="Bank Detail",
    ondelete='set null'  # Ensures safe deletion of referenced bank.detail
    )


    # Custom shipping terms field
    shipping_terms = fields.Selection(
        selection=[('EXW', 'EXW'), ('FOB', 'FOB'), ('CNF', 'CNF'), ('CIF', 'CIF')],
        string='Shipping Term',
        default='FOB',
    )

    # container_no = fields.Char(string="Container Number")
    container_no = fields.Char(string='Container Number')
    # container_carrier = fields.Char(string='Container Carrier')
    container_cbm = fields.Char(string="Container CBM")
    destination = fields.Char(string="POL")
    delivery = fields.Char(string="POD")
    fda = fields.Char(string="FDA")

    language_instructions = fields.Char(string="Language Instructions")
    lot_code = fields.Char(string="Lot Code")
    producer_code = fields.Char(string="Producer Code")
    fi_number = fields.Char(string="FI Number")
    loading_port = fields.Char(string="Loading Port")
    port_of_discharge = fields.Char(string="Port Of Discharge")
    # fi_date = fields.Date(string="FI Date")
    fi_date = fields.Date(string='FI Date')
    required_date = fields.Date(
        string='Required Date',
        default=lambda self: fields.Date.to_string(fields.Date.context_today(self) + timedelta(days=7))
    )
    order_date = fields.Date(string='Export Order Date')
    container_arrival_date = fields.Date(string='Container Arrival Date')
    manufactory_date = fields.Date(string='Manufactory Date')
    expiry_date = fields.Date(string='Expiry Date')
    best_before = fields.Date(string='Best Before Date')
    print_instruction = fields.Char(string="Print Instruction")
    bl_no = fields.Char(string="BL Number")
    bl_date = fields.Date(string='BL Date')
    validity = fields.Date(string='Validity Date')
    delivery_date = fields.Date(string='Delivery Date')
    vessel_voyage = fields.Char(string="Vessel and Voyage")
    vessel = fields.Char(string="Vessel")
    shipment = fields.Char(string="Shipment")
    voyage = fields.Char(string="Voyage")
    terms = fields.Text(string="Terms & Condition")
    container_type = fields.Selection([
        ('20fcl', '20FCL'),
        ('40fcl', '40FCL'),
        ('45hc', '45HC'),
        ('lcl', 'LCL'),
       
    ], string='Container Type', required=True, default='lcl')

    freight = fields.Float(string="Freight")
    gross_total = fields.Float(
        string="Gross Total",
        compute="_compute_gross_total",
        store=True
    )
    # frieght_description = fields.Char(string="Frieght Reason")
    discount = fields.Float(string="Discount")
    # discount_description = fields.Char(string="Discount Reason")
    total = fields.Float(string="Total Amount", compute="_compute_total")
    total_qty = fields.Float(string="Total Quantity", compute="_compute_total_qty")
    total_net_weight = fields.Float(string="Total Net Weight", compute="_compute_total_net_weight")
    total_gross_weight = fields.Float(string="Total Gross Weight", compute="_compute_total_gross_weight")
    total_in_words = fields.Char(string="Total in Words", compute="_compute_amount_to_words", store=True)
    customer_container = fields.Char(string="Customer Container No.")
    label_name = fields.Char(string="PACKETS / LABELS FOR PRODUCTS' NAME")
    pi_mm_yyyy = fields.Char(string="MM-YYYY", compute="_compute_pi_mm_yyyy")
    pi_no = fields.Char(string="PI No", compute="_compute_pi_no")
    partner_code = fields.Char(string="Partner Code", related='partner_id.ref', readonly=True)
    is_mtj_company = fields.Boolean(string="Is MTJ Company", compute="_compute_is_mtj_company")
    total_cbm = fields.Float(string="Total CBM", compute="_compute_total_cbm")
    total_order_cbm = fields.Float(string="Total Order CBM", compute="_compute_total_order_cbm")

    shipping_line = fields.Char(string="Shipping Lline")
    total_items = fields.Integer(string="Total Items", compute="_compute_total_items")
    
    assignee_ids = fields.Many2many(
        'res.users',
        string='Assignees',
        tracking=True,
        help="People responsible for this order"
    )
    
    export_order_categories = fields.Many2many(
        'product.category',
        string='Export Order Categories',
        help='Deprecated: Export Order is now driven by Export Category Tags.',
    )

    export_order_category_tags = fields.Many2many(
        'product.category.tag',
        string='Export Category Tags',
        help='Which export category tags to include on the Export Order PDF. Each product needs an Export Category Tag set on its template.',
    )
    
    discount_reason = fields.Text(string="Discount Reason")
    freight_reason = fields.Text(string="Freight Reason")
    credit_note_amount = fields.Float(string="Credit Note")
    credit_note_description = fields.Text(string="Credit Note Description")
    
    signature_type = fields.Selection([
        ('system', 'System Generated'),
        ('user',   'User Signature'),
    ], default='system', string='Signature Type')

    
    def action_custom_save(self):
        """ Custom save action """
        return True  # Odoo automatically saves records when an action is performed.


    @api.onchange('container_type', 'total_order_cbm','total_qty')
    def _onchange_cbm_limit(self):
        for record in self:
            if record.container_type == '20fcl' and record.total_order_cbm > 27:
                return {
                    'warning': {
                        'title': "CBM Exceeds Limit",
                        'message': "The Total CBM exceeds the limit for 20FCL (27 CBM). Please check your data.",
                    }
                }
            elif record.container_type == '40fcl' and record.total_order_cbm > 65:
                return {
                    'warning': {
                        'title': "CBM Exceeds Limit",
                        'message': "The Total CBM exceeds the limit for 40FCL (65 CBM). Please check your data.",
                    }
                }
            elif record.container_type == '45hc' and record.total_order_cbm > 75:
                return {
                    'warning': {
                        'title': "CBM Exceeds Limit",
                        'message': "The Total CBM exceeds the limit for 45HC (75 CBM). Please check your data.",
                    }
                }
            elif record.container_type == 'lcl' and record.total_order_cbm >= 20:
                return {
                    'warning': {
                        'title': "CBM Exceeds Limit",
                        'message': "The Total CBM exceeds the limit for LCL (20 CBM). Please check your data.",
                    }
                }

            elif record.container_type == '20fcl' and record.total_order_cbm < 20:
                return {
                    'warning': {
                        'title': "CBM Below Container Capacity",
                        'message': "The Total CBM is below 20 CBM. You may consider selecting 'LCL' instead of '20FCL' to optimize container usage.",
                    }
                }


    @api.depends('order_line')
    def _compute_total_items(self):
        for order in self:
            order.total_items = len(order.order_line)

    

    @api.depends('company_id', 'company_id.name')
    def _compute_is_mtj_company(self):
        for record in self:
            company_name = (record.company_id.name or '').strip()
            record.is_mtj_company = company_name == 'MTJ' or company_name.startswith('MTJ ')

    @api.depends('customer_container', 'partner_code')
    def _compute_pi_mm_yyyy(self):
        current_month = datetime.now().strftime('%m')
        current_year = datetime.now().strftime('%Y')
        value = f"{current_month}-{current_year}"
        for record in self:
            record.pi_mm_yyyy = value

    @api.depends('customer_container', 'partner_code')
    def _compute_pi_no(self):
        for record in self:
            if record.customer_container and record.partner_code:
                current_month = datetime.now().strftime('%m')  # Current month in MM format
                current_year = datetime.now().strftime('%Y')  # Current year in YYYY format
                record.pi_no = f"{record.partner_code}/{record.customer_container}/{current_month}-{current_year}"
            else:
                record.pi_no = ''


    # sum of cbm
    @api.depends('order_line.order_cbm')  # Correct dependency on related model
    def _compute_total_order_cbm(self):
        order_cbm = 0
        for record in self.order_line:
            order_cbm += record.order_cbm
        self.total_order_cbm = order_cbm

    # sum of cbm
    @api.depends('order_line.cbm')  # Correct dependency on related model
    def _compute_total_cbm(self):
        cbm = 0
        for record in self.order_line:
            cbm += record.cbm
        self.total_cbm = cbm




    @api.depends('order_line.net_weight')  # Correct dependency on related model
    def _compute_total_net_weight(self):
        for order in self:
            order.total_net_weight = sum(line.net_weight for line in order.order_line)

    

    @api.depends('order_line.gross_weight')  # Correct dependency on related model
    def _compute_total_gross_weight(self):
        for order in self:
            order.total_gross_weight = sum(line.gross_weight for line in order.order_line)

    @api.onchange('freight')
    def add_total_value(self):
        self.tax_totals['amount_total'] = self.freight + self.tax_totals['amount_total']
        print(f"test{self.tax_totals['amount_total']}{self.freight}")

    @api.depends('amount_total')
    def _compute_total_qty(self):
        qty = 0
        for record in self.order_line:
            qty += record.product_uom_qty
        self.total_qty = qty

    @api.depends('freight', 'discount', 'credit_note_amount', 'order_line.price_subtotal')
    def _compute_total(self):
        for record in self:
            line_total = sum(record.order_line.mapped('price_subtotal'))  # Sum of all order_line price_subtotal
            record.total = (record.freight + line_total - record.credit_note_amount) - record.discount


    @api.depends('total','total_qty','discount','freight')
    def _compute_amount_to_words(self):
        for record in self:
            record.total_in_words = num2words(record.total)
            
    # def get_report_action(self):
    #     """ Override to always hide the print button """
    #     action = super().get_report_action()
    #     action['config'] = False  # This will hide the print button
    #     return action
    
    # def _get_report_action(self, report, data=None):
    #     """ Completely disable printing for all Sales Orders """
    #     return False
    
    # def get_report_action(self):
    #     """ Completely disable printing for all sales orders """
    #     action = super().get_report_action()
    #     # Remove print options
    #     action['config'] = False
    #     # Remove all report types (PDF, Excel, etc.)
    #     if 'report_type' in action:
    #         del action['report_type']
    #     return action


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        # Check if user is in 'Sale/Customer Group'
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            # Search for partner linked to current user
            partner = self.env['res.partner'].search(
                ['|', ('user_id', '=', self.env.uid), ('user_ids', 'in', self.env.uid)],
                limit=1,
            )
            if partner:
                res['partner_id'] = partner.id

        return res


    @api.model
    def create(self, vals):
        # also enforce on create
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            partner = self.env['res.partner'].search(
                ['|', ('user_id', '=', self.env.uid), ('user_ids', 'in', self.env.uid)],
                limit=1,
            )
            if partner:
                vals['partner_id'] = partner.id
        return super(SaleOrder, self).create(vals)

    def write(self, vals):
        # strip out any attempt to change partner_id
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            vals.pop('partner_id', None)
        return super(SaleOrder, self).write(vals)
    
    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            form_view = res.get('views', {}).get('form', {})
            if form_view:
                arch = form_view.get('arch', '')
                old = 'name="partner_id"'
                new = 'name="partner_id" domain="[(\'user_id\', \'=\', uid), (\'customer_rank\', \'&gt;\', 0)]"'
                if old in arch and new not in arch:
                    res['views']['form']['arch'] = arch.replace(old, new, 1)
        return res

    @api.depends('order_line.price_subtotal')
    def _compute_gross_total(self):
        for order in self:
            order.gross_total = sum(line.price_subtotal for line in order.order_line)
