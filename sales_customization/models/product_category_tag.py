from odoo import fields, models


class ProductCategoryTag(models.Model):
    _name = 'product.category.tag'
    _description = 'Export Category Tag'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
