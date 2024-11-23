from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BankDetail(models.Model):
    _name = 'bank.detail'
    _inherit = ['mail.thread']
    _description = "Bank Detail"
    _rec_name = 'bank_name'

    # Fields
    bank_name = fields.Char(string="Bank Name")
    branch = fields.Char(string="Branch")
    account_title = fields.Char(string="Account Title")
    account_no = fields.Char(string="Account No")
    swift_code = fields.Char(string="Swift Code")
    iban = fields.Char(string="IBAN #")

    def unlink(self):
        for record in self:
            linked_sales = self.env['sale.order'].search([('bank_detail_id', '=', record.id)])
            if linked_sales:
                raise ValidationError(
                    "You cannot delete this Bank Detail because it is linked to one or more Sales Orders."
                )
        return super(BankDetail, self).unlink()


