from odoo import api, fields, models
from odoo.exceptions import UserError


class DistributorOrderLine(models.Model):
    _name = 'distributor.order.line'
    _description = 'Distributor Order Line'
    _order = 'id'

    order_id = fields.Many2one(
        comodel_name='distributor.order',
        string='Distributor Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        domain=[('sale_ok', '=', True)],
        change_default=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        store=True,
        readonly=True,
    )
    product_qty = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        required=True,
        default=1.0,
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
        required=True,
        default=0.0,
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
        digits='Account',
    )
    description = fields.Text(string='Description')

    # read-only mirror of parent state – used for UI visibility rules
    order_state = fields.Selection(
        related='order_id.state',
        string='Order State',
        store=False,
    )

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit

    def _get_product_catalog_lines_data(self, **kwargs):
        if len(self) == 1:
            return {
                'quantity': self.product_qty,
                'price': self.price_unit,
                'readOnly': self.order_id._is_readonly(),
                'uomDisplayName': self.product_uom_id.display_name,
            }
        elif self:
            self.product_id.ensure_one()
            return {
                'readOnly': True,
                'price': self[0].product_id.lst_price,
                'quantity': sum(
                    self.mapped(
                        lambda line: line.product_uom_id._compute_quantity(
                            qty=line.product_qty,
                            to_unit=line.product_id.uom_id,
                        )
                    )
                ),
                'uomDisplayName': self.product_id.uom_id.display_name,
            }
        return {
            'quantity': 0,
        }

    def action_add_from_catalog(self):
        order = self.order_id[:1] or self.env['distributor.order'].browse(self.env.context.get('order_id'))
        if not order:
            raise UserError('Please save the distributor order before opening the catalog.')
        return order.with_context(child_field='order_line_ids').action_add_from_catalog()

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price
            self.description = self.product_id.description_sale or ''
