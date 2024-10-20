from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    launch_date = fields.Date(string='Launch Date')
    hs_code = fields.Char(string='HS Code')
    packaging_detail_id = fields.Many2one('packaging.detail', string="Packaging Detail")
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
    
