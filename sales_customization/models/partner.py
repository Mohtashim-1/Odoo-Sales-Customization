from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    image_field_1 = fields.Image("Company Logo 1")
    port = fields.Char("Port")
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    old_sale_ids = fields.One2many(
        'crm.lead.old.sale',
        'partner_id',
        string='Old Sales',
    )
    old_sale_count = fields.Integer(
        string='Old Sales Count',
        compute='_compute_old_sales',
        store=False,
    )
    old_sale_total = fields.Monetary(
        string='Old Sales Total',
        currency_field='currency_id',
        compute='_compute_old_sales',
        store=False,
    )
    sale_order_count = fields.Integer(
        string='Sale Orders',
        compute='_compute_sale_orders',
        store=False,
    )
    sale_order_total = fields.Monetary(
        string='Sale Orders Total',
        currency_field='currency_id',
        compute='_compute_sale_orders',
        store=False,
    )
    last_sale_date = fields.Date(
        string='Last Sale Date',
        compute='_compute_sale_orders',
        store=False,
    )
    user_ids = fields.Many2many(
        'res.users',
        'res_partner_user_rel',
        'partner_id',
        'user_id',
        string='Users',
        help='Additional users assigned to this partner.',
    )

    brand_id = fields.Many2one(
        'product.brand',
        string='Customer Brand',
    )
    # code = fields.Char("code")

    def action_custom_save(self):
        """ Custom save action """
        return True  # Odoo automatically saves records when an action is performed.

    @api.depends('old_sale_ids.invoice_value')
    def _compute_old_sales(self):
        for partner in self:
            total = sum(partner.old_sale_ids.mapped('invoice_value'))
            partner.old_sale_total = total
            partner.old_sale_count = len(partner.old_sale_ids)

    def _compute_sale_orders(self):
        SaleOrder = self.env['sale.order']
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
            ]
            data = SaleOrder.read_group(
                domain,
                ['amount_total:sum'],
                []
            )
            partner.sale_order_total = data[0].get('amount_total', 0.0) if data else 0.0
            partner.sale_order_count = SaleOrder.search_count(domain)
            last_order = SaleOrder.search(domain, order='date_order desc', limit=1)
            partner.last_sale_date = last_order.date_order.date() if last_order else False

    def action_open_old_sales_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Old Sales Analysis',
            'res_model': 'crm.lead.old.sale',
            'view_mode': 'graph,pivot,tree',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'search_default_group_by_invoice_date': 1,
            },
        }

    def action_open_sale_orders_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Orders Analysis',
            'res_model': 'sale.order',
            'view_mode': 'graph,pivot,tree',
            'domain': [
                ('partner_id', '=', self.id),
                ('state', 'in', ['sale', 'done']),
            ],
            'context': {
                'search_default_groupby_date_order': 1,
            },
        }

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].title()  # Capitalize Name
        return super(ResPartner, self).create(vals)

    # @api.onchange('name')
    # def _onchange_name_set_ref(self):
    #     """
    #     Automatically set the `ref` field to the first letter of the `name` field.
    #     """
    #     for record in self:
    #         if record.name:
    #             # Get the first letter of each word in the name
    #             record.ref = ''.join(word[0] for word in record.name.split())
    @api.onchange('name')
    def _onchange_name_set_ref(self):
        """
        Automatically set the `ref` field to the first 3 letters from the first letter of each word in the `name` field.
        """
        for record in self:
            if record.name:
                # Get the first letter of each word
                initials = ''.join(word[0] for word in record.name.split())
                # Limit to 3 letters
                record.ref = initials[:3]


    @api.model
    def create(self, vals):
        """
        Set the `ref` field based on the `name` field during creation.
        """
        if 'name' in vals and vals['name']:
            vals['ref'] = ''.join(word[0] for word in vals['name'].split())
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        """
        Update the `ref` field based on the `name` field when the partner is updated.
        """
        if 'name' in vals and vals['name']:
            vals['ref'] = ''.join(word[0] for word in vals['name'].split())
        return super(ResPartner, self).write(vals)
    
    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].title()  # Capitalize Name
        return super(ResPartner, self).write(vals)

    
    
