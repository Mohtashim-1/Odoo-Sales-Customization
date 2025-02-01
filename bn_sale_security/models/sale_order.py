from odoo import models, fields, api, exceptions


SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('approved', "Approved"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class Sale(models.Model):
    _inherit = 'sale.order'


    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')


    def action_approve(self):
        self.state = 'approved' 