from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    image_field_1 = fields.Image("Company Logo 1")
    port = fields.Char("Port")
    # code = fields.Char("code")

    def action_custom_save(self):
        """ Custom save action """
        return True  # Odoo automatically saves records when an action is performed.

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].title()  # Capitalize Name
        return super(ResPartner, self).create(vals)

    # @api.onchange('name')
    # def _onchange_name_set_ref(self):
    #     """
    #     Automatically set the `ref` field to the first letter of the `name` field.
    #     """
    #     for record in self:
    #         if record.name:
    #             # Get the first letter of each word in the name
    #             record.ref = ''.join(word[0] for word in record.name.split())
    @api.onchange('name')
    def _onchange_name_set_ref(self):
        """
        Automatically set the `ref` field to the first 3 letters from the first letter of each word in the `name` field.
        """
        for record in self:
            if record.name:
                # Get the first letter of each word
                initials = ''.join(word[0] for word in record.name.split())
                # Limit to 3 letters
                record.ref = initials[:3]


    @api.model
    def create(self, vals):
        """
        Set the `ref` field based on the `name` field during creation.
        """
        if 'name' in vals and vals['name']:
            vals['ref'] = ''.join(word[0] for word in vals['name'].split())
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        """
        Update the `ref` field based on the `name` field when the partner is updated.
        """
        if 'name' in vals and vals['name']:
            vals['ref'] = ''.join(word[0] for word in vals['name'].split())
        return super(ResPartner, self).write(vals)
    
    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].title()  # Capitalize Name
        return super(ResPartner, self).write(vals)

    
    
