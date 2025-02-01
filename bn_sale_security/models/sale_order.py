from odoo import models, fields, api, exceptions


SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('review', "Review Quotation"),
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


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        raise exceptions.ValidationError('Hit')

        """Override search to only show approved orders"""
        args.append(('state', '=', 'approved'))  # Add filter for approved orders
        return super(Sale, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent', 'approved'}

    def action_review_quotation(self):
        self.state = 'review'

    def action_approve(self):
        self.state = 'approved' 