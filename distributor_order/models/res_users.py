from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    distributor_allowed_brand_ids = fields.Many2many(
        comodel_name='product.brand',
        relation='res_users_distributor_allowed_brand_rel',
        column1='user_id',
        column2='brand_id',
        string='Distributor order brands',
        help='When this user is a Distributor User (not Salesperson), distributor order lines and '
             'the product catalog only offer products whose template brand is one of these. '
             'Leave empty to allow any product.',
    )
