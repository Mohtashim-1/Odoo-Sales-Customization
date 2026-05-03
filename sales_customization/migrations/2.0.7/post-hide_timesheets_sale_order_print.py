# -*- coding: utf-8 -*-

def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    ts_report = env.ref(
        "sale_timesheet.timesheet_report_sale_order", raise_if_not_found=False
    )
    if ts_report:
        ts_report.write({"binding_model_id": False})
