from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vat = fields.Char(string="Customer VAT", related='partner_id.vat', readonly=True)

    address = fields.Char(string="Address", related='partner_id.vat', readonly=True)


    # Custom shipping terms field
    shipping_terms = fields.Selection(
        selection=[('EXW', 'EXW'), ('FOB', 'FOB'), ('CNF', 'CNF'), ('CIF', 'CIF')],
        string='Shipping Term',
        default='FOB',
    )

    container_no = fields.Char(string="Container Number")
    container_cbm = fields.Char(string="Container CBM")
    destination = fields.Char(string="Destination")
    delivery = fields.Char(string="Delivery")

    language_instructions = fields.Char(string="Language Instructions")
    lot_code = fields.Char(string="Lot Code")
    producer_code = fields.Char(string="Producer Code")
    fi_number = fields.Char(string="FI Number")
    loading_port = fields.Char(string="Loading Port")
    port_of_discharge = fields.Char(string="Port Of Discharge")

    # freight_charges = fields.Float(string="Freight Charges", default=0.0)

    # total = fields.Float(string="Total", default=0.0)

    

    # @api.depends('order_line.price_total', 'tax_totals', 'freight_charges')
    # def _compute_amount(self):
    #     self.total = self.amount_total - self.freight_charges
    #     # for order in self:
    #     #     super(SaleOrder, order)._compute_amount()
    #     #     order.amount_total += order.freight_charges

    
    # freight_charge = fields.Float(string="Freight Charge")

    # @api.depends('order_line.price_total', 'freight_charge')
    # def _compute_amount_all(self):
    #     super(SaleOrder, self)._compute_amount_all()
    #     for order in self:
    #         order.amount_total += order.freight_charge