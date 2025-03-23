from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'


    image_field_1 = fields.Image("Company Logo 1")
    image_field_2 = fields.Image("Company Logo 2")
    image_field_3 = fields.Image("Sign")
    image_field_4 = fields.Image("Image")
    # fda_numbers = fields.Integer("FDA Numbers")
    # bank_name = fields.Char(string="FDA")
#    fda_numbers = fields.Char("FDA Numbers")
