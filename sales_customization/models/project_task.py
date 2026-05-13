from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    export_order_date = fields.Date(string='Export Order Date')
    container_arrival_date = fields.Date(string='Container Arrival Date')
    container_arrival_warning = fields.Boolean(
        compute='_compute_container_arrival_warning',
        store=False,
    )
    container_days_left_text = fields.Char(
        compute='_compute_container_arrival_warning',
        store=False,
    )

    def _compute_container_arrival_warning(self):
        today = fields.Date.today()
        for task in self:
            if task.container_arrival_date:
                delta = (task.container_arrival_date - today).days
                task.container_arrival_warning = 0 <= delta <= 10
                task.container_days_left_text = f"{delta} days left for shipment"
            else:
                task.container_arrival_warning = False
                task.container_days_left_text = False
