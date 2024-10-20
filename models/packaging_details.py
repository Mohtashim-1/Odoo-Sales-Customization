from odoo import models, fields

class PackagingDetails(models.Model):
    _name = 'packaging.detail'
    _inherit = ['mail.thread']
    _description = "Packaging Detail"


    net_weight= fields.Float(string="Net Weight")
    no_of_pieces= fields.Float(string="No Of Pieces")
    weight= fields.Float(string="Carton")
    packaging_detail= fields.Char(string="Packaging Details")


    
