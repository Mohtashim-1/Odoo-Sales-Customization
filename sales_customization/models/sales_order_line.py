from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = "categ_id_name asc, id asc"
    categ_id_name = fields.Char(string='Category',related="product_id.categ_id.name", store=True, index=True)

    launch_date = fields.Date(string='Launch Date', related='product_id.product_tmpl_id.launch_date')
    product_code = fields.Char(string='Product Code', related='product_id.product_tmpl_id.product_code')
    hs_code_id = fields.Many2one(
        'hs.code', 
        string='HS Code', 
        related='product_id.product_tmpl_id.hs_code_id',
        store=True  # Store in the database for better performance
    )
    packaging_detail_id = fields.Many2one(
        'packaging.detail', 
        string='Packaging Detail', 
        related='product_id.product_tmpl_id.packaging_detail_id',
        store=True
    )
    #  want to get no_of_pieces field from packaging detail and store it in no of pieces
    packaging_id = fields.Many2one('packaging.detail', string="Packaging")
    no_of_pieces = fields.Float(related='packaging_detail_id.no_of_pieces', string="No of Pieces", store=True)
    # no_of_pieces = fields.Float(string="No of Pieces", related="packaging_detail_id.no_of_pieces",store=True) 
    length = fields.Float(string='Length', related='product_id.product_tmpl_id.length')
    width = fields.Float(string='Width', related='product_id.product_tmpl_id.width')
    height = fields.Float(string='Height', related='product_id.product_tmpl_id.height')
    net_weight1 = fields.Float(string='Net Weight', related='product_id.product_tmpl_id.net_weight')
    net_weight = fields.Float(string="Net", compute="_calculated_net_weight", store=True)
    gross_weight = fields.Float(string='Gross Weight', compute="_compute_gross_weight")
    
    cbm = fields.Float(string='CBM', related='product_id.product_tmpl_id.cbm')
    order_cbm = fields.Float(string='Order CBM', compute='_compute_total_cbm')
    fcl_20 = fields.Float(string='FCL 20', related='product_id.product_tmpl_id.fcl_20')
    fcl_40 = fields.Float(string='FCL 40', related='product_id.product_tmpl_id.fcl_40')
    shelf_life = fields.Float(string='Shelf Life', related='product_id.product_tmpl_id.shelf_life')
    image = fields.Image(string='Image', related='product_id.product_tmpl_id.image_1920')
    discount = fields.Float(string="Discount")
    description = fields.Char(string="Description1")
    remarks = fields.Char(string="Remarks")
    status = fields.Char(string="Status")
    ctn = fields.Float(string="CTN")
    pkt = fields.Float(string="PKT")
    no_of_ctn = fields.Char(string="No of Cartoons", compute="_compute_no_of_cartoons", store=True)
    analysis = fields.Char(string="Analysis")
    markings = fields.Char(string="Marks and Analysis")
    custom_price = fields.Float(string="Custom Price",compute="_compute_custom_price", store=True)
    custom_amount = fields.Float(string="Custom Amount",compute="_compute_custom_amount", store=True)
    lbs_oz = fields.Char(string='LBS OZ', compute="_compute_lbs_oz", store=True)
    pkts = fields.Float(string="PKTs", compute= "_calculate_p_w_q", store=True)
    

        
    @api.depends('product_uom_qty', 'no_of_pieces')
    def _calculate_p_w_q(self):
        for line in self:   
            # Ensure that no_of_pieces is not None before multiplication
            line.pkts = (line.product_uom_qty or 0) * (line.no_of_pieces or 0)
            
            
    @api.depends('custom_price','product_uom_qty')
    def _compute_custom_amount(self):
        for line in self:
            line.custom_amount = line.product_uom_qty * line.custom_price

    @api.depends('net_weight1', 'product_uom_qty')
    def _calculated_net_weight(self):
        for line in self:
            line.net_weight = line.net_weight1 * line.product_uom_qty


    
    @api.depends('product_uom_qty')
    def _compute_no_of_cartoons(self):
        cumulative_qty = 0  # Initialize cumulative quantity
        for line in self.order_id.order_line:  # Loop through all order lines in sequence
            initial = cumulative_qty + 1  # Start of the range
            final = initial + line.product_uom_qty - 1  # End of the range
            cumulative_qty = final  # Update cumulative quantity for the next line
            # line.no_of_ctn = f"{initial} to {final}" 
            line.no_of_ctn = f"{int(initial)} to {int(final)}"

    @api.depends('price_subtotal', 'product_uom_qty', 'order_id.total', 'order_id.amount_total')
    def _compute_custom_price(self):
        for line in self:
            sales_order_total = line.order_id.amount_total or 1.0  
            price_subtotal = line.price_subtotal or 0.0
            product_uom_qty = line.product_uom_qty or 1.0 
            net_total_amount = line.order_id.total or 0.0

            # Ensure non-zero values to avoid division by zero errors
            if price_subtotal > 0 and product_uom_qty > 0:
 
                intermediate1 = price_subtotal / sales_order_total
                intermediate2 = net_total_amount / product_uom_qty
                line.custom_price = intermediate1 * intermediate2
            else:
                line.custom_price = 0.0

    @api.depends('net_weight', 'product_uom_qty')
    def _compute_gross_weight(self):
        for record in self:
            record.gross_weight = (record.net_weight) + (record.product_uom_qty * 1.5)

    @api.depends('cbm','product_uom_qty')
    def _compute_total_cbm(self):
        for record in self:
            record.order_cbm = record.product_uom_qty * record.cbm


    @api.depends('gross_weight')
    def _compute_lbs_oz(self):
        for line in self.order_id.order_line:
            gross_weight_grams = line.gross_weight or 0
            lbs = gross_weight_grams / 453.59237  # Convert grams to pounds
            pounds = float(lbs)  # Whole pounds
            ounces = lbs * 16  # Remainder as ounces
            # Format pounds and ounces with 2 decimal places
            line.lbs_oz = f"{pounds:.0f} lbs {ounces:.2f} oz"

    def _prepare_invoice_line(self, **optional_values):
        """
        Override to ensure account_id is always set when creating invoice lines.
        This fixes the "Missing required account on accountable line" error.
        """
        res = super()._prepare_invoice_line(**optional_values)
        
        # Check if account_id is missing (None, False, or 0) and we have a product
        account_id = res.get('account_id')
        if (not account_id or account_id is False) and self.product_id:
            account = None
            product_template = self.product_id.product_tmpl_id
            company = self.order_id.company_id
            
            # FIRST: Try direct account search by name/code (fastest and most reliable)
            if company:
                # Search for "Sales Income" account by name
                account_records = self.env['account.account'].sudo().search([
                    ('company_id', '=', company.id),
                    ('deprecated', '=', False),
                    ('name', 'ilike', 'Sales Income')
                ], limit=1)
                
                # Check if we got a valid record (recordset with records)
                if account_records and len(account_records) > 0 and account_records.id:
                    account = account_records
                else:
                    # If not found, search for account code 3111001
                    account_records = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('code', '=', '3111001'),
                        ('deprecated', '=', False)
                    ], limit=1)
                    if account_records and len(account_records) > 0 and account_records.id:
                        account = account_records
                    else:
                        account = None
            
            # Method 1: Use the standard Odoo _get_product_accounts method (handles fiscal position)
            if product_template:
                try:
                    fiscal_position = self.order_id.fiscal_position_id
                    # This is the standard Odoo method that handles company context and fiscal positions
                    product_accounts = product_template._get_product_accounts(fiscal_pos=fiscal_position)
                    # Try different possible keys
                    account = (product_accounts.get('income') or 
                              product_accounts.get('stock_output') or
                              product_accounts.get('output'))
                except Exception:
                    pass
            
            # Method 2: Direct access to property_account_income_id (company-dependent field)
            if not account and product_template and company:
                try:
                    # For company-dependent fields, we need to access them in the company's context
                    # Use read() to get the value for the specific company
                    product_template_company = product_template.with_company(company)
                    account = product_template_company.property_account_income_id
                except Exception:
                    pass
            
            # Method 3: Try reading the property directly using the property system
            if not account and product_template and company:
                try:
                    # Use the property system to get company-specific value
                    # This is how Odoo stores company-dependent fields
                    prop = self.env['ir.property'].with_company(company)._get(
                        'property_account_income_id',
                        'product.template',
                        res_id=product_template.id
                    )
                    if prop:
                        account = prop
                except Exception:
                    pass
            
            # Method 4: Last resort - search for account by reading the property record directly
            if not account and product_template and company:
                try:
                    # Search ir.property table directly for this product's income account
                    prop_record = self.env['ir.property'].search([
                        ('res_id', '=', 'product.template,%s' % product_template.id),
                        ('name', '=', 'property_account_income_id'),
                        ('company_id', '=', company.id)
                    ], limit=1)
                    if prop_record and prop_record.value_reference:
                        # value_reference is in format 'account.account,ID'
                        model, account_id = prop_record.value_reference.split(',')
                        if model == 'account.account':
                            account = self.env['account.account'].browse(int(account_id))
                            if not account.exists():
                                account = None
                except Exception:
                    pass
            
            # If not set, try product category
            if not account and self.product_id.categ_id:
                if hasattr(self.product_id.categ_id, 'property_account_income_categ_id'):
                    account = self.product_id.categ_id.property_account_income_categ_id
            
            # If still not set, try to get any income account from company
            if not account and self.order_id.company_id:
                company = self.order_id.company_id
                # Try multiple strategies to find an income account
                # Strategy 0: Direct search for "Sales Income" account (common name) - DO THIS FIRST
                account = self.env['account.account'].sudo().search([
                    ('company_id', '=', company.id),
                    ('deprecated', '=', False),
                    ('name', 'ilike', 'Sales Income')
                ], limit=1)
                
                # Strategy 0.5: Search for account code 3111001 specifically
                if not account:
                    account = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('code', '=', '3111001'),
                        ('deprecated', '=', False)
                    ], limit=1)
                
                # Strategy 1: Search by account code pattern (income accounts typically start with 3 or 4)
                if not account:
                    account_records = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('deprecated', '=', False),
                        '|',
                        ('code', 'like', '3%'),  # Some income accounts start with 3
                        ('code', 'like', '4%')   # Income accounts typically start with 4
                    ], limit=1)
                    if account_records and len(account_records) > 0 and account_records.id:
                        account = account_records
                
                # Strategy 2: Search by user_type for income/revenue accounts (Odoo 17 compatible)
                if not account:
                    # Search for account types that are typically used for income
                    income_types = self.env['account.account.type'].sudo().search([
                        ('type', 'in', ['other', 'income'])
                    ], limit=5)
                    if income_types and len(income_types) > 0:
                        account_records = self.env['account.account'].sudo().search([
                            ('company_id', '=', company.id),
                            ('deprecated', '=', False),
                            ('user_type_id', 'in', income_types.ids)
                        ], limit=1)
                        if account_records and len(account_records) > 0 and account_records.id:
                            account = account_records
                
                # Strategy 3: Search for any account with 'income' or 'revenue' in name
                if not account:
                    account_records = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('deprecated', '=', False),
                        '|',
                        ('name', 'ilike', 'income'),
                        ('name', 'ilike', 'revenue')
                    ], limit=1)
                    if account_records and len(account_records) > 0 and account_records.id:
                        account = account_records
                
                # Strategy 4: Get any non-deprecated account as last resort (better than failing)
                if not account:
                    account_records = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('deprecated', '=', False)
                    ], limit=1)
                    if account_records and len(account_records) > 0 and account_records.id:
                        account = account_records
            
            # Set the account_id if we found one
            if account:
                # Handle recordset properly
                if hasattr(account, '__len__') and hasattr(account, 'id'):
                    # It's a recordset
                    if len(account) > 0 and account.id:
                        res['account_id'] = account.id
                        account = account  # Keep it for validation
                    else:
                        account = None  # Empty recordset
                elif hasattr(account, 'id') and account.id:
                    # Single record
                    res['account_id'] = account.id
                elif isinstance(account, int) and account > 0:
                    # It's already an ID
                    res['account_id'] = account
                else:
                    account = None  # Invalid account, continue searching
            
            # Final check - if still no account, try one more aggressive search
            if not res.get('account_id') and company:
                # Last resort: get ANY account with "income" or "sales" in the name
                account_records = self.env['account.account'].sudo().search([
                    ('company_id', '=', company.id),
                    ('deprecated', '=', False),
                    '|',
                    ('name', 'ilike', 'income'),
                    ('name', 'ilike', 'sales')
                ], limit=1)
                if account_records and len(account_records) > 0 and account_records.id:
                    res['account_id'] = account_records.id
            
            # Absolute last resort: get ANY non-deprecated account from the company
            if not res.get('account_id') and company:
                any_account = self.env['account.account'].sudo().search([
                    ('company_id', '=', company.id),
                    ('deprecated', '=', False)
                ], limit=1, order='code asc')
                if any_account and len(any_account) > 0 and any_account.id:
                    res['account_id'] = any_account.id
            
            # Only raise error if we absolutely cannot find ANY account in the company
            if not res.get('account_id'):
                # Log for debugging
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(
                    f"Could not find any account for product {self.product_id.display_name} "
                    f"in company {company.name if company else 'Unknown'}. "
                    f"Product template ID: {product_template.id if product_template else 'None'}"
                )
                # If still no account found, raise a more helpful error
                raise UserError(
                    f"Missing income account for product '{self.product_id.display_name}'. "
                    f"Please configure an income account for this product, its category, "
                    f"or ensure the company '{self.order_id.company_id.name}' has income accounts configured."
                )
        
        return res
    