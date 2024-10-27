from odoo import models, fields

class HSCode(models.Model):
    _name = 'hs.code'
    _description = "HS Code"
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Ensure to inherit from mail.thread for chatter

    name = fields.Char(string="HS Code", required=True, tracking=True)  # Enable tracking
    description = fields.Text(string="Description", tracking=True)  # Enable tracking
