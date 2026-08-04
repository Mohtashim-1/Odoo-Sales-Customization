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
    is_mtj_company = fields.Boolean(
        string="Is MTJ Company",
        compute="_compute_is_mtj_company",
        store=True,
    )
    use_order_currency = fields.Boolean(
        string="Use Order Currency",
        compute="_compute_use_order_currency",
        store=True,
        help="MTJ and VPPL export companies can choose Order Currency independently.",
    )
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

    collection_tag_id = fields.Many2one(
        'product.category.tag',
        string='Collection',
        help='Deprecated: use Collection on each order line (product category).',
    )
    price_selection = fields.Selection(
        selection=[
            ('fob_usd', 'FOB PRICE IN USD'),
            ('ddp_usd', 'DDP PRICE IN USD'),
            ('local_pkr', 'LOCAL PRICE IN PKR'),
        ],
        string='Price Selection',
        default='fob_usd',
    )
    price_selection_label = fields.Char(
        string='Price Selection',
        compute='_compute_price_selection_label',
    )
    total_value_label = fields.Char(
        string='Total Value Label',
        compute='_compute_total_value_label',
    )
    mtj_price_currency_id = fields.Many2one(
        'res.currency',
        string='Price Currency',
        compute='_compute_mtj_price_currency_id',
        store=True,
        help='Currency of the selected product price (FOB/DDP = USD, Local = PKR).',
    )
    mtj_exchange_rate = fields.Float(
        string='Exchange Rate',
        digits=(12, 6),
        default=1.0,
        help='1 unit of Price Currency equals this many units of Order Currency.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        inverse='_inverse_mtj_currency_id',
        store=True,
        readonly=False,
        ondelete='restrict',
    )

    
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

    

    @api.model
    def _company_allows_order_currency(self, company):
        """MTJ + VPPL export companies can select Order Currency freely."""
        name = (company.name or '').strip()
        if name == 'MTJ' or name.startswith('MTJ '):
            return True
        name_lower = name.lower()
        return 'vital products' in name_lower or 'eastern products' in name_lower

    @api.depends('company_id', 'company_id.name')
    def _compute_is_mtj_company(self):
        for record in self:
            company_name = (record.company_id.name or '').strip()
            record.is_mtj_company = company_name == 'MTJ' or company_name.startswith('MTJ ')

    @api.depends('company_id', 'company_id.name')
    def _compute_use_order_currency(self):
        for record in self:
            record.use_order_currency = self._company_allows_order_currency(record.company_id)

    @api.depends('pricelist_id', 'company_id', 'use_order_currency', 'is_mtj_company', 'price_selection')
    def _compute_currency_id(self):
        regular_orders = self.filtered(lambda order: not order.use_order_currency)
        if regular_orders:
            super(SaleOrder, regular_orders)._compute_currency_id()
        for order in self.filtered('use_order_currency'):
            if not order.currency_id:
                if order.is_mtj_company:
                    order.currency_id = (
                        order._mtj_get_price_currency() or order.company_id.currency_id
                    )
                else:
                    order.currency_id = order.company_id.currency_id

    def _inverse_mtj_currency_id(self):
        """Allow MTJ/VPPL users to pick the order currency independently of the pricelist."""
        return

    @api.depends('price_selection')
    def _compute_price_selection_label(self):
        labels = dict(self._fields['price_selection'].selection)
        for order in self:
            order.price_selection_label = labels.get(order.price_selection, '')

    @api.depends('price_selection', 'is_mtj_company', 'use_order_currency', 'currency_id')
    def _compute_total_value_label(self):
        for order in self:
            currency_name = (order.currency_id.name if order.currency_id else None) or 'USD'
            if order.is_mtj_company and order.price_selection == 'local_pkr':
                order.total_value_label = f'Total Value ({currency_name})'
            elif order.is_mtj_company:
                order.total_value_label = f'Net DDP Value in {currency_name}'
            elif order.use_order_currency:
                order.total_value_label = f'Net FOB Value in {currency_name}'
            else:
                order.total_value_label = 'Total Amount'

    @api.depends('price_selection', 'is_mtj_company', 'use_order_currency', 'company_id')
    def _compute_mtj_price_currency_id(self):
        for order in self:
            if order.is_mtj_company and order.price_selection:
                order.mtj_price_currency_id = order._mtj_get_price_currency()
            elif order.use_order_currency:
                # VPPL: product/list prices are stored in company currency (usually USD).
                order.mtj_price_currency_id = order.company_id.currency_id
            else:
                order.mtj_price_currency_id = False

    def _mtj_get_price_currency(self):
        self.ensure_one()
        if self.price_selection == 'local_pkr':
            return self.env['res.currency'].search([('name', '=', 'PKR')], limit=1)
        return self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

    def _mtj_get_currency(self):
        return self._mtj_get_price_currency()

    def _mtj_conversion_date(self):
        self.ensure_one()
        return self.date_order.date() if self.date_order else fields.Date.context_today(self)

    def _mtj_ensure_currency_rates(self):
        """Fetch today's rates when the order currency has no rate yet."""
        self.ensure_one()
        if not self.use_order_currency or not self.currency_id:
            return
        rate_date = self._mtj_conversion_date()
        Rate = self.env['res.currency.rate'].sudo()
        currencies_to_check = (self.mtj_price_currency_id | self.currency_id).filtered(
            lambda currency: currency != self.company_id.currency_id
        )
        missing = currencies_to_check.filtered(
            lambda currency: not Rate.search_count([
                ('currency_id', '=', currency.id),
                ('company_id', '=', self.company_id.id),
                ('name', '<=', rate_date),
            ])
        )
        if missing:
            self.env['res.currency']._mtj_update_company_rates(self.company_id, rate_date)

    def _mtj_set_default_exchange_rate(self):
        self.ensure_one()
        from_currency = self.mtj_price_currency_id or (
            self._mtj_get_price_currency() if self.is_mtj_company else self.company_id.currency_id
        )
        to_currency = self.currency_id
        if not from_currency or not to_currency or from_currency == to_currency:
            self.mtj_exchange_rate = 1.0
            return
        self._mtj_ensure_currency_rates()
        self.mtj_exchange_rate = from_currency._convert(
            1.0,
            to_currency,
            self.company_id,
            self._mtj_conversion_date(),
        ) or 1.0

    def _mtj_convert_amount(self, amount):
        self.ensure_one()
        from_currency = self.mtj_price_currency_id or (
            self._mtj_get_price_currency() if self.is_mtj_company else self.company_id.currency_id
        )
        to_currency = self.currency_id
        if not amount or not from_currency or not to_currency:
            return amount
        if from_currency == to_currency:
            return amount
        if self.mtj_exchange_rate and self.mtj_exchange_rate > 0:
            return amount * self.mtj_exchange_rate
        return from_currency._convert(
            amount,
            to_currency,
            self.company_id,
            self._mtj_conversion_date(),
        )

    def _apply_mtj_prices_to_lines(self):
        self.filtered('is_mtj_company').order_line._apply_mtj_price_from_product()

    def _mtj_currency_for_selection(self, price_selection):
        if price_selection == 'local_pkr':
            return self.env['res.currency'].search([('name', '=', 'PKR')], limit=1)
        return self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

    @api.onchange('price_selection')
    def _onchange_mtj_price_selection(self):
        for order in self.filtered('is_mtj_company'):
            order._mtj_set_default_exchange_rate()
            order._apply_mtj_prices_to_lines()

    @api.onchange('currency_id', 'date_order')
    def _onchange_mtj_currency_id(self):
        for order in self.filtered('use_order_currency'):
            order._mtj_set_default_exchange_rate()
            if order.is_mtj_company:
                order._apply_mtj_prices_to_lines()

    @api.onchange('mtj_exchange_rate')
    def _onchange_mtj_exchange_rate(self):
        self.filtered('is_mtj_company')._apply_mtj_prices_to_lines()

    @api.onchange('collection_tag_id')
    def _onchange_mtj_collection_tag_id(self):
        """Legacy header collection — filtering is on order lines via collection_categ_id."""
        return {}

    def action_add_from_catalog(self):
        return super().action_add_from_catalog()

    @api.model
    def _normalize_partner_code_for_pi(self, value):
        """Partner code on PI No is always max 3 characters (from partner Internal Reference)."""
        code = (value or '').strip()
        if not code:
            return ''
        return code[:3]

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
            partner_code = record._normalize_partner_code_for_pi(record.partner_code)
            if record.customer_container and partner_code:
                current_month = datetime.now().strftime('%m')
                current_year = datetime.now().strftime('%Y')
                record.pi_no = (
                    f"{partner_code}/{record.customer_container}/{current_month}-{current_year}"
                )
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


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.user.has_group('sales_customization.sales_customer_group'):
                partner = self.env['res.partner'].search(
                    ['|', ('user_id', '=', self.env.uid), ('user_ids', 'in', self.env.uid)],
                    limit=1,
                )
                if partner:
                    vals['partner_id'] = partner.id
            company = self.env['res.company'].browse(
                vals.get('company_id') or self.env.company.id
            )
            if self._company_allows_order_currency(company) and not vals.get('currency_id'):
                company_name = (company.name or '').strip()
                is_mtj = company_name == 'MTJ' or company_name.startswith('MTJ ')
                if is_mtj:
                    price_selection = vals.get('price_selection', 'fob_usd')
                    price_currency = self._mtj_currency_for_selection(price_selection)
                    if price_currency:
                        vals['currency_id'] = price_currency.id
                elif company.currency_id:
                    vals['currency_id'] = company.currency_id.id
        orders = super().create(vals_list)
        for order in orders.filtered('use_order_currency'):
            order._mtj_set_default_exchange_rate()
            if order.is_mtj_company:
                order.order_line._apply_mtj_price_from_product()
        return orders

    def write(self, vals):
        # strip out any attempt to change partner_id
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            vals.pop('partner_id', None)
        res = super(SaleOrder, self).write(vals)
        currency_orders = self.filtered('use_order_currency')
        if currency_orders and any(
            field in vals
            for field in ('price_selection', 'currency_id', 'mtj_exchange_rate', 'date_order')
        ):
            for order in currency_orders:
                if 'mtj_exchange_rate' not in vals and any(
                    field in vals for field in ('price_selection', 'currency_id', 'date_order')
                ):
                    order._mtj_set_default_exchange_rate()
            currency_orders.filtered('is_mtj_company').order_line._apply_mtj_price_from_product()
        return res
    
    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if self.env.user.has_group('sales_customization.sales_customer_group'):
            form_view = res.get('views', {}).get('form', {})
            arch = form_view.get('arch')
            if arch:
                from lxml import etree
                root = etree.fromstring(arch if isinstance(arch, bytes) else arch.encode('utf-8'))
                # Replace domain in-place (do not inject a second domain= attribute)
                for node in root.xpath("//field[@name='partner_id']"):
                    node.set(
                        'domain',
                        "['&', ('customer_rank', '>', 0), "
                        "'|', ('user_id', '=', uid), ('user_ids', 'in', uid)]",
                    )
                    break
                form_view['arch'] = etree.tostring(root, encoding='unicode')
        return res

    @api.depends('order_line.price_subtotal')
    def _compute_gross_total(self):
        for order in self:
            order.gross_total = sum(line.price_subtotal for line in order.order_line)
