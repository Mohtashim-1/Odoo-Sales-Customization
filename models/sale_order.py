from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Add a related field to fetch 'vat' from the customer (res.partner)
    customer_vat = fields.Char(
        string="Customer VAT",
        related='partner_id.vat',  # Fetching 'vat' field from 'res.partner'
        store=True,                # If you want to store it in the database
        readonly=True              # Make it readonly if needed
    )