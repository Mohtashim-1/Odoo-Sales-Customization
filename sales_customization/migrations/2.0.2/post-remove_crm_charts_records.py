# -*- coding: utf-8 -*-

def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})

    xmlids = [
        'sales_customization.menu_crm_charts_by_team',
        'sales_customization.menu_crm_charts_dashboard',
        'sales_customization.action_crm_lead_charts_dashboard_by_team',
        'sales_customization.action_crm_lead_charts_dashboard',
        'sales_customization.action_crm_lead_charts_dashboard_view_tree',
        'sales_customization.action_crm_lead_charts_dashboard_view_pivot',
        'sales_customization.action_crm_lead_charts_dashboard_view_graph',
        'sales_customization.crm_lead_view_graph_dashboard_team',
        'sales_customization.crm_lead_view_graph_dashboard_stage',
    ]

    for xmlid in xmlids:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.unlink()
