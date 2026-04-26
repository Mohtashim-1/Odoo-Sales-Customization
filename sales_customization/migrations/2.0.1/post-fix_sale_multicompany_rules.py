# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Sale multi-company rules use ``company_ids`` (= active companies in the switcher only).

    After changing ``sale.order.company_id`` to another allowed company, a re-read can fail
    if that company is not currently active in the UI. Re-scope rules to all companies the
    user is allowed to access (``user.company_ids``).
    """
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    domain_mc = (
        "['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]"
    )
    for xmlid in (
        "sale.sale_order_comp_rule",
        "sale.sale_order_line_comp_rule",
        "sale.sale_order_report_comp_rule",
    ):
        rule = env.ref(xmlid, raise_if_not_found=False)
        if rule:
            rule.write({"domain_force": domain_mc})
