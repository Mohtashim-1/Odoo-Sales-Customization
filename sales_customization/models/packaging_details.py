from odoo import models, fields, api

class PackagingDetails(models.Model):
    _name = 'packaging.detail'
    _inherit = ['mail.thread']
    _description = "Packaging Detail"
    _rec_name = 'packaging_detail'

    net_weight = fields.Float(string="Net Weight", tracking=True)
    no_of_pieces = fields.Float(string="No Of Pieces", tracking=True)
    weight = fields.Float(string="Carton", tracking=True)
    packaging_detail = fields.Char(string="Packaging Details", compute="_compute_packaging_detail", store=True, tracking=True)

    @api.depends('net_weight', 'no_of_pieces', 'weight')
    def _compute_packaging_detail(self):
        for record in self:
            if record.net_weight and record.no_of_pieces and record.weight:
                # Calculate and set packaging_detail with multiplication result
                result = record.net_weight * record.no_of_pieces * record.weight
                record.packaging_detail = f"{record.net_weight} X {record.no_of_pieces} X {record.weight}"
            else:
                record.packaging_detail = "0.00"
