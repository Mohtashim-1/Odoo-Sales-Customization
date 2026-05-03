from odoo import _, api, models
from odoo.exceptions import AccessError


class CrmTag(models.Model):
    _inherit = 'crm.tag'
    _allowed_tag_creator_email = 'shoaibmohtashim973@gmail.com'

    @api.model_create_multi
    def create(self, vals_list):
        # Restrict CRM tag creation to one specific user.
        user = self.env.user
        if user.login != self._allowed_tag_creator_email and user.email != self._allowed_tag_creator_email:
            raise AccessError(_('Only the designated user can create CRM tags.'))
        return super().create(vals_list)
