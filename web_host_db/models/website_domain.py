from odoo import api, models


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _normalize_stored_domain(self, domain):
        domain = (domain or '').strip()
        for prefix in ('https://', 'http://'):
            if domain.lower().startswith(prefix):
                domain = domain[len(prefix):]
        return domain.rstrip('/')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('domain'):
                vals['domain'] = self._normalize_stored_domain(vals['domain'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('domain'):
            vals = dict(vals)
            vals['domain'] = self._normalize_stored_domain(vals['domain'])
        return super().write(vals)
