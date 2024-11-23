from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    launch_date = fields.Date(string='Launch Date')
    product_code = fields.Char(string='Product Code',compute='_compute_product_code', store=True)
    # hs_code = fields.Char(string='HS Code')
    hs_code_id = fields.Many2one('hs.code', string="HS Code")
    packaging_detail_id = fields.Many2one('packaging.detail', string="Packaging Detail")
    packaging_weight = fields.Float('Packaging Weight' , related='packaging_detail_id.net_weight')
    packaging_no_of_pc = fields.Float('Packaging No of Pcs' , related='packaging_detail_id.no_of_pieces')
    packaging_cartoon = fields.Float('Packaging Cartoon' , related='packaging_detail_id.weight')
    length = fields.Float(string="Length")
    width= fields.Float(string="Width")
    height= fields.Float(string="Height")
    net_weight= fields.Float(string="Net Weight")
    gross_weight= fields.Float(string="Gross Weight")
    cbm= fields.Float(string="CBM")
    order_cbm= fields.Float(string="Order CBM")
    fcl_20 = fields.Float(string="40ft FCL HQ")
    fcl_40 = fields.Float(string="20ft FCL HQ")
    shelf_life = fields.Float(string="Shelf Life")

    @api.depends('name')
    def _compute_product_code(self):
        for record in self:
            if record.name:
                # Split the name by spaces and take the first letter of each word
                first_letters = ''.join(word[0].upper() for word in record.name.split() if word)
                record.product_code = first_letters
            else:
                record.product_code = ''
    
