from odoo import models, fields, api

class BankDetail(models.Model):
    _name = 'bank.detail'
    _inherit = ['mail.thread']
    _description = "Bank Detail"
    _rec_name = 'bank_name'

    bank_name = fields.Char(string="Bank Name")
    branch = fields.Char(string="Brank")
    account_title = fields.Char(string="Account Title")
    account_no = fields.Char(string="Account No")
    swift_code = fields.Char(string="Swift Code")
    iban = fields.Char(string="IBAN #")

