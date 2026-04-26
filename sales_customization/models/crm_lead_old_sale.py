from odoo import _, fields, models
from odoo.exceptions import UserError


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

    def action_sync_partner_from_lead(self):
        """Copy address and contact fields from the lead onto the linked customer."""
        field_map = (
            ('email_from', 'email'),
            ('phone', 'phone'),
            ('mobile', 'mobile'),
            ('street', 'street'),
            ('street2', 'street2'),
            ('city', 'city'),
            ('zip', 'zip'),
            ('state_id', 'state_id'),
            ('country_id', 'country_id'),
            ('website', 'website'),
            ('function', 'function'),
            ('title', 'title'),
        )
        for lead in self:
            if not lead.partner_id:
                raise UserError(_('Set a customer on the lead before syncing.'))
            vals = {}
            for lead_field, partner_field in field_map:
                vals[partner_field] = getattr(lead, lead_field)
            if lead.lang_code:
                vals['lang'] = lead.lang_code
            if lead.partner_id.is_company:
                if lead.partner_name:
                    vals['name'] = lead.partner_name
            else:
                name = (lead.contact_name or lead.partner_name or '').strip()
                if name:
                    vals['name'] = name
            lead.partner_id.write(vals)
            lead.message_post(
                body=_('Customer “%s” was updated from this lead (address & contact fields).')
                % lead.partner_id.display_name,
            )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Customer synced'),
                'message': _('Contact details were copied from the lead to the customer.'),
                'type': 'success',
                'sticky': False,
            },
        }

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

    def action_open_crm_charts_dashboard(self):
        action = self.env.ref(
            'sales_customization.action_crm_lead_charts_dashboard',
            raise_if_not_found=False,
        )
        return action.read()[0] if action else False
