from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    distributor_portal_user_count = fields.Integer(
        string='Distributor users',
        compute='_compute_distributor_portal_user_count',
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

    @api.depends('is_distributor', 'commercial_partner_id')
    def _compute_distributor_portal_user_count(self):
        Users = self.env['res.users'].sudo()
        Dist = self.env.ref('distributor_order.group_distributor_user')
        for partner in self:
            if not partner.is_distributor:
                partner.distributor_portal_user_count = 0
                continue
            commercial = partner.commercial_partner_id
            partner.distributor_portal_user_count = Users.search_count([
                ('partner_id', 'child_of', commercial.id),
                ('groups_id', 'in', [Dist.id]),
            ])

    def _distributor_portal_email(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        return (commercial.email or self.email or '').strip()

    def _get_existing_distributor_users(self, commercial):
        """Users already linked to this commercial entity with Distributor User rights."""
        Dist = self.env.ref('distributor_order.group_distributor_user')
        Users = self.env['res.users'].sudo()
        return Users.search([
            ('partner_id', 'child_of', commercial.id),
            ('groups_id', 'in', [Dist.id]),
        ])

    def _ensure_internal_user_groups(self, user, dist_group, ctx):
        """Set Internal User + Distributor groups.

        Odoo computes ``share`` from ``base.group_user`` on ``groups_id`` only — not from implied
        groups alone until saved — so the Access Rights / User Type widget stays blank unless
        ``base.group_user`` is explicitly present (see ``res.users._compute_share``).
        """
        user_group = self.env.ref('base.group_user')
        portal_g = self.env.ref('base.group_portal')
        gids = [g for g in user.groups_id.ids if g != portal_g.id]
        if user_group.id not in gids:
            gids.append(user_group.id)
        if dist_group.id not in gids:
            gids.append(dist_group.id)
        # Keep catalog group explicit: (6,0,gids) can otherwise drop implied-only links until recomputed.
        catalog_g = self.env.ref('distributor_order.group_distributor_catalog_reader', raise_if_not_found=False)
        if catalog_g and dist_group.id in gids and catalog_g.id not in gids:
            gids.append(catalog_g.id)
        user.with_context(**ctx).write({'groups_id': [(6, 0, gids)]})

    def _ensure_distributor_user(self):
        """Create or align an Internal User (not Portal) with Distributor User group."""
        if self.env.context.get('skip_distributor_portal_hook'):
            return
        dist_group = self.env.ref('distributor_order.group_distributor_user')
        Users = self.env['res.users'].sudo()
        ctx = dict(self.env.context, skip_distributor_portal_hook=True)

        for partner in self:
            commercial = partner.commercial_partner_id
            email = partner._distributor_portal_email()

            existing = partner._get_existing_distributor_users(commercial)
            if existing:
                for user in existing:
                    partner._ensure_internal_user_groups(user, dist_group, ctx)
                continue

            if not email:
                raise UserError(_(
                    'Set an email address on this contact or company before enabling distributor.'
                ))

            login_user = Users.search([('login', '=', email)], limit=1)
            if login_user:
                if login_user.partner_id.commercial_partner_id.id != commercial.id:
                    raise UserError(_(
                        'This email is already used by another login (%s). '
                        'Use a different email for this distributor.',
                        login_user.login,
                    ))
                login_user.with_context(**ctx).write({'partner_id': commercial.id})
                partner._ensure_internal_user_groups(login_user, dist_group, ctx)
                try:
                    login_user.with_context(**ctx).action_reset_password()
                except Exception:
                    pass
                continue

            # New user: Internal User (base.group_user) + Distributor — required for share=False / UI radios.
            internal_g = self.env.ref('base.group_user')
            catalog_g = self.env.ref('distributor_order.group_distributor_catalog_reader')
            new_user = Users.with_context(
                **ctx,
                no_reset_password=True,
                mail_create_nolog=True,
            ).create({
                'name': commercial.name or partner.name,
                'login': email,
                'email': email,
                'partner_id': commercial.id,
                'groups_id': [(6, 0, [internal_g.id, dist_group.id, catalog_g.id])],
            })
            try:
                new_user.with_context(**ctx).action_reset_password()
            except Exception:
                pass

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

    def action_view_distributor_portal_users(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        Dist = self.env.ref('distributor_order.group_distributor_user')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Distributor users'),
            'res_model': 'res.users',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'child_of', commercial.id),
                ('groups_id', 'in', [Dist.id]),
            ],
            'context': {'create': False},
        }

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if not self.env.context.get('skip_distributor_portal_hook'):
            partners.filtered('is_distributor')._ensure_distributor_user()
        return partners

    def write(self, vals):
        if hasattr(self, '_merge_default_property_accounts_for_write'):
            self._merge_default_property_accounts_for_write(vals)
        res = super().write(vals)
        if self.env.context.get('skip_distributor_portal_hook'):
            return res
        sync_user = 'is_distributor' in vals or 'email' in vals
        if sync_user:
            self.filtered('is_distributor')._ensure_distributor_user()
        return res
