from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(compute='_compute_ref', store=True)

    @api.depends('name')
    def _compute_ref(self):
        for record in self:
            if record.name:
                record.ref = ''.join(word[0].upper() for word in record.name.split())
            else:
                record.ref = '12'


    # code = fields.Char(strings="Code")

