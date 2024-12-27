from odoo import models, fields, api

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

    gross_weight = fields.Float(string='Gross Weight', compute="_compute_gross_weight")
    
    cbm = fields.Float(string='CBM', related='product_id.product_tmpl_id.cbm')
    order_cbm = fields.Float(string='Order CBM', compute='_compute_total_cbm')
    fcl_20 = fields.Float(string='FCL 20', related='product_id.product_tmpl_id.fcl_20')
    fcl_40 = fields.Float(string='FCL 40', related='product_id.product_tmpl_id.fcl_40')
    shelf_life = fields.Float(string='Shelf Life', related='product_id.product_tmpl_id.shelf_life')
    image = fields.Image(string='Image', related='product_id.product_tmpl_id.image_1920')
    discount = fields.Float(string="Discount")
    description = fields.Char(string="Description1")
    remarks = fields.Char(string="Remarks")
    status = fields.Char(string="Status")
    ctn = fields.Float(string="CTN")
    pkt = fields.Float(string="PKT")
    no_of_ctn = fields.Char(string="No of Cartoons")
    analysis = fields.Char(string="Analysis")
    markings = fields.Char(string="Marks and Analysis")
    custom_price = fields.Float(string="Custom Price",compute="_compute_custom_price", store=True)
    # lbs_oz = fields.Char(string='LBS OZ', related='product_id.product_tmpl_id.lbs')
    # school_image = fields.Image("School Image")
    # image = fields.Image(string='Image', related='product_id.product_tmpl_id.image_1920', readonly=True)

    @api.depends('product_uom_qty')
    def _compute_no_of_cartoons(self):
        cumulative_qty = 0  # Initialize cumulative quantity
        for line in self.order_id.order_line:  # Loop through all order lines in sequence
            initial = cumulative_qty + 1  # Start of the range
            final = initial + line.product_uom_qty - 1  # End of the range
            cumulative_qty = final  # Update cumulative quantity for the next line
            line.no_of_ctn = f"{initial} to {final}"  # Set the computed range for the line

    @api.depends('price_subtotal', 'product_uom_qty', 'order_id.total', 'order_id.amount_total')
    def _compute_custom_price(self):
        for line in self:
            sales_order_total = line.order_id.amount_total or 1.0  
            price_subtotal = line.price_subtotal or 0.0
            product_uom_qty = line.product_uom_qty or 1.0 
            net_total_amount = line.order_id.total or 0.0

            # Ensure non-zero values to avoid division by zero errors
            if price_subtotal > 0 and product_uom_qty > 0:
 
                intermediate1 = price_subtotal / sales_order_total
                intermediate2 = net_total_amount / product_uom_qty
                line.custom_price = intermediate1 * intermediate2
            else:
                line.custom_price = 0.0

    @api.depends('net_weight', 'product_uom_qty')
    def _compute_gross_weight(self):
        for record in self:
            record.gross_weight = (record.net_weight) + (record.product_uom_qty * 1.5)

    @api.depends('cbm','product_uom_qty')
    def _compute_total_cbm(self):
        for record in self:
            record.order_cbm = record.product_uom_qty * record.cbm

    