from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_distributor = fields.Boolean(
        string='Is Distributor',
        default=False,
        help='Check this box to mark the partner as a distributor.',
    )
    distributor_salesperson_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned Salesperson',
        domain=[('share', '=', False)],
        help='Internal salesperson responsible for reviewing and approving orders from this distributor.',
    )
    distributor_order_ids = fields.One2many(
        comodel_name='distributor.order',
        inverse_name='distributor_id',
        string='Distributor Orders',
    )
    distributor_order_count = fields.Integer(
        string='Orders',
        compute='_compute_distributor_order_count',
    )

    def _compute_distributor_order_count(self):
        data = self.env['distributor.order'].read_group(
            [('distributor_id', 'in', self.ids)],
            ['distributor_id'],
            ['distributor_id'],
        )
        mapped = {d['distributor_id'][0]: d['distributor_id_count'] for d in data}
        for rec in self:
            rec.distributor_order_count = mapped.get(rec.id, 0)

    def action_view_distributor_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Distributor Orders',
            'res_model': 'distributor.order',
            'view_mode': 'list,form',
            'domain': [('distributor_id', '=', self.id)],
            'context': {'default_distributor_id': self.id},
        }
