from odoo import models, fields, api

class ShippingTerms(models.Model):
    _name = 'shipping.term'
    _inherit = ['mail.thread']
    _description = "Shipping Term"
    _rec_name = 'shipping_term'

    shipping_term = fields.Char(string="Shipping Term", tracking=True)
    

    # @api.depends('net_weight', 'no_of_pieces', 'weight')
    # def _compute_packaging_detail(self):
    #     for record in self:
    #         if record.net_weight and record.no_of_pieces and record.weight:
    #             # Calculate and set packaging_detail with multiplication result
    #             result = record.net_weight * record.no_of_pieces * record.weight
    #             record.packaging_detail = f"{record.net_weight} X {record.no_of_pieces} X {record.weight}"
    #         else:
    #             record.packaging_detail = "0.00"
