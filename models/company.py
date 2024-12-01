from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'


    image_field_1 = fields.Image("Company Logo 1")
    image_field_2 = fields.Image("Company Logo 2")
