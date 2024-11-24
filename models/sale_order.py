from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vat = fields.Char(string="Customer VAT", related='partner_id.vat', readonly=True)

    address = fields.Char(string="Address", related='partner_id.vat', readonly=True)

    bank_detail_id = fields.Many2one(
    'bank.detail',
    string="Bank Detail",
    ondelete='set null'  # Ensures safe deletion of referenced bank.detail
    )


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
    fda = fields.Char(string="FDA")

    language_instructions = fields.Char(string="Language Instructions")
    lot_code = fields.Char(string="Lot Code")
    producer_code = fields.Char(string="Producer Code")
    fi_number = fields.Char(string="FI Number")
    loading_port = fields.Char(string="Loading Port")
    port_of_discharge = fields.Char(string="Port Of Discharge")
    # fi_date = fields.Date(string="FI Date")
    fi_date = fields.Date(string='FI Date')
    bl_no = fields.Char(string="BL Number")
    bl_date = fields.Date(string='BL Date')
    validity = fields.Date(string='Validity Date')
    delivery_date = fields.Date(string='Delivery Date')
    vessel_voyage = fields.Char(string="Vessel and Voyage")
    vessel = fields.Char(string="Vessel")
    voyage = fields.Char(string="Voyage")
    terms = fields.Text(string="Terms & Condition")

    freight = fields.Float(string="Freight")
    discount = fields.Float(string="Discount")
    total = fields.Float(string="Total1", compute="_compute_total")
    total_qty = fields.Float(string="Total Quantity", compute="_compute_total_qty")
    total_net_weight = fields.Float(string="Total Net Weight", compute="_compute_total_net_weight")
    total_gross_weight = fields.Float(string="Total Gross Weight", compute="_compute_total_gross_weight")

    @api.depends('order_line.net_weight')  # Correct dependency on related model
    def _compute_total_net_weight(self):
        for order in self:
            order.total_net_weight = sum(line.net_weight for line in order.order_line)

    @api.depends('order_line.gross_weight')  # Correct dependency on related model
    def _compute_total_gross_weight(self):
        for order in self:
            order.total_gross_weight = sum(line.gross_weight for line in order.order_line)

    # @api.depends('net_weight')
    # def _compute_total_net_weight(self):
    #     net_weight = 0
    #     for record in self.order_line:
    #         net_weight += record.net_weight
    #     self.total_net_weight = net_weight

    # @api.depends('gross_weight')
    # def _compute_total_gross_weight(self):
    #     gross_weight = 0
    #     for record in self.order_line:
    #         gross_weight += record.gross_weight
    #     self.total_gross_weight = gross_weight

    @api.onchange('freight')
    def add_total_value(self):
        self.tax_totals['amount_total'] = self.freight + self.tax_totals['amount_total']
        print(f"test{self.tax_totals['amount_total']}{self.freight}")

    @api.depends('amount_total')
    def _compute_total_qty(self):
        qty = 0
        for record in self.order_line:
            qty += record.product_uom_qty
        self.total_qty = qty

        
        


    @api.depends('freight')
    def _compute_total(self):
        for record in self:
            record.total = record.freight + record.amount_total
            # print(f"total_1: {record.amount_total}")