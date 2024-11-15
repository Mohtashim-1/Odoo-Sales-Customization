from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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
    length = fields.Float(string='Length', related='product_id.product_tmpl_id.length')
    width = fields.Float(string='Width', related='product_id.product_tmpl_id.width')
    height = fields.Float(string='Height', related='product_id.product_tmpl_id.height')
    net_weight = fields.Float(string='Net Weight', related='product_id.product_tmpl_id.net_weight')
    gross_weight = fields.Float(string='Gross Weight', related='product_id.product_tmpl_id.gross_weight')
    cbm = fields.Float(string='CBM', related='product_id.product_tmpl_id.cbm')
    order_cbm = fields.Float(string='Order CBM', related='product_id.product_tmpl_id.order_cbm')
    fcl_20 = fields.Float(string='FCL 20', related='product_id.product_tmpl_id.fcl_20')
    fcl_40 = fields.Float(string='FCL 40', related='product_id.product_tmpl_id.fcl_40')
    shelf_life = fields.Float(string='Shelf Life', related='product_id.product_tmpl_id.shelf_life')
    image = fields.Image(string='Image', related='product_id.product_tmpl_id.image_1920')
    discount = fields.Float(string="Discount")
    description = fields.Char(string="Description")
    remarks = fields.Char(string="Remarks")
    status = fields.Char(string="Status")
    ctn = fields.Float(string="CTN")
    pkt = fields.Float(string="PKT")
    no_of_ctn = fields.Char(string="No of Cartoons")
    analysis = fields.Char(string="Analysis")
    # school_image = fields.Image("School Image")
    # image = fields.Image(string='Image', related='product_id.product_tmpl_id.image_1920', readonly=True)

