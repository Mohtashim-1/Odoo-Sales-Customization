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

    # @api.depends('net_weight', 'no_of_pieces', 'weight')
    # def _compute_packaging_detail(self):
    #     for record in self:
    #         if record.net_weight and record.no_of_pieces and record.weight:
    #             # Calculate and set packaging_detail with multiplication result
    #             result = record.net_weight * record.no_of_pieces * record.weight
    #             record.packaging_detail = f"{record.net_weight} GM X {record.no_of_pieces} POUCH X {record.weight} CTN"
    #         else:
    #             record.packaging_detail = "0.00"

    @api.depends('net_weight', 'no_of_pieces', 'weight')
    def _compute_packaging_detail(self):
        for record in self:
            if record.net_weight and record.no_of_pieces and record.weight:
                # Format numbers to remove decimals if they are whole numbers
                net_weight = int(record.net_weight) if record.net_weight.is_integer() else record.net_weight
                no_of_pieces = int(record.no_of_pieces) if record.no_of_pieces.is_integer() else record.no_of_pieces
                weight = int(record.weight) if record.weight.is_integer() else record.weight
                
                # Set the packaging_detail field
                record.packaging_detail = f"{net_weight} GM X {no_of_pieces} POUCH X {weight} CTN"
            else:
                record.packaging_detail = "0 GM X 0 POUCH X 0 CTN"
