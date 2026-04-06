from odoo import fields, models


class CrmLeadOldSale(models.Model):
    _name = 'crm.lead.old.sale'
    _description = 'CRM Lead Old Sale'
    _order = 'invoice_date desc, id desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='lead_id.partner_id',
        store=True,
        readonly=True,
    )
    old_sales = fields.Char(string='Old Sales')
    invoice_date = fields.Date(string='Date')
    invoice_number = fields.Char(string='Invoice #')
    currency_id = fields.Many2one(
        'res.currency',
        related='lead_id.company_id.currency_id',
        store=True,
        readonly=True,
    )
    invoice_value = fields.Monetary(string='Invoice Value', currency_field='currency_id')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    old_sale_ids = fields.One2many(
        'crm.lead.old.sale',
        'lead_id',
        string='Old Sales',
    )

    def action_open_customer_dashboard(self):
        self.ensure_one()
        if not self.partner_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Dashboard',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }
