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
    cbm= fields.Float(string="CBM", compute="_compute_cbm")

    net_weight= fields.Float(string="Net Weight", compute="_compute_net_weight")
    gross_weight= fields.Float(string="Gross Weight")
    # lbs = fields.Float(string="Pounds")

    # lbs = fields.Char(string='LBS Oz')
    # lbs = fields.char(strings="LBS OZ")
    
    order_cbm= fields.Float(string="Order CBM")

    fcl_20 = fields.Float(string="20ft FCL HQ", compute="_compute_20fcl")
    fcl_40 = fields.Float(string="40ft FCL HQ", compute="_compute_40fcl")
    shelf_life = fields.Float(string="Shelf Life", default = 3)

    @api.depends('name')
    def _compute_product_code(self):
        for record in self:
            if record.name:
                # Split the name by spaces and take the first letter of each word
                first_letters = ''.join(word[0].upper() for word in record.name.split() if word)
                record.product_code = first_letters
            else:
                record.product_code = ''

    # net_weight = (packaging_weight * packaging_no_of_pc * packaging_cartoon) / 1000

    @api.depends('packaging_weight', 'packaging_no_of_pc', 'packaging_cartoon')
    def _compute_net_weight(self):
        for record in self:
            if record.packaging_weight and record.packaging_no_of_pc and record.packaging_cartoon:
                record.net_weight = (
                    record.packaging_weight * 
                    record.packaging_no_of_pc * 
                    record.packaging_cartoon
                ) / 1000
            else:
                record.net_weight = 0.0

    @api.depends('length','width','height')
    def _compute_cbm(self):
        for record in self:
            if record.length and record.width and record.height:
                record.cbm = (
                    record.length *
                    record.width *
                    record.height
                ) / 1000000
            else:
                record.cbm = 0.0
    
    # calculate 20 fcl

    @api.depends('cbm')
    def _compute_20fcl(self):
        for record in self:
            if record.cbm:
                record.fcl_20 = 27 / record.cbm 
            else:
                record.fcl_20 = 0

    # calculate 40 fcl

    @api.depends('cbm')
    def _compute_40fcl(self):
        for record in self:
            if record.cbm:
                record.fcl_40 = 65 / record.cbm 
            else:
                record.fcl_40 = 0


