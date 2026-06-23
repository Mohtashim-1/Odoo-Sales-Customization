# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Remove Sales Administrator from the legacy duplicate Export01 login."""
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    legacy_user = env['res.users'].sudo().search(
        [('login', '=', 'export01@vitaltea.com.pk'), ('active', '=', True)],
        limit=1,
    )
    if not legacy_user:
        return

    canonical_user = env['res.users'].sudo().search(
        [('login', '=', 'Export01@vitaltea.com.pk'), ('active', '=', True)],
        limit=1,
    )
    if not canonical_user or legacy_user.id == canonical_user.id:
        return

    sales_manager = env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
    if sales_manager and sales_manager in legacy_user.groups_id:
        legacy_user.write({'groups_id': [(3, sales_manager.id)]})
