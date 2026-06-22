import base64
import csv
import io
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class OldSalesExportWizard(models.TransientModel):
    _name = 'old.sales.export.wizard'
    _description = 'Old Sales Excel Export Wizard'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    partner_ids = fields.Many2many('res.partner', string='Customers')

    def _get_export_domain(self):
        domain = []
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        return domain

    def action_export_excel(self):
        self.ensure_one()
        domain = self._get_export_domain()
        records = self.env['crm.lead.old.sale'].search(domain, order='partner_id, invoice_date desc, id desc')
        if not records:
            raise UserError(_('No old sales records found for the selected filters.'))

        headers = [
            'Customer',
            'Customer Email',
            'Country',
            'Old Sales',
            'Invoice Date',
            'Invoice #',
            'Invoice Value',
            'Currency',
            'CRM Lead',
        ]

        output = io.BytesIO()
        if xlsxwriter:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Old Sales')

            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#366092',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
            })
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
            })
            money_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0.00',
            })
            date_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'num_format': 'yyyy-mm-dd',
            })

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            total_value = sum(float(rec.invoice_value or 0.0) for rec in records)

            for row, rec in enumerate(records, 1):
                partner = rec.partner_id
                invoice_value = float(rec.invoice_value or 0.0)
                worksheet.write(row, 0, partner.display_name or '', cell_format)
                worksheet.write(row, 1, partner.email or '', cell_format)
                worksheet.write(row, 2, partner.country_id.name or '', cell_format)
                worksheet.write(row, 3, rec.old_sales or '', cell_format)
                if rec.invoice_date:
                    worksheet.write_datetime(
                        row, 4,
                        datetime.combine(rec.invoice_date, datetime.min.time()),
                        date_format,
                    )
                else:
                    worksheet.write(row, 4, '', cell_format)
                worksheet.write(row, 5, rec.invoice_number or '', cell_format)
                worksheet.write(row, 6, invoice_value, money_format)
                worksheet.write(row, 7, rec.currency_id.name or '', cell_format)
                worksheet.write(row, 8, rec.lead_name or '', cell_format)

            worksheet.set_column(0, 0, 28)
            worksheet.set_column(1, 1, 24)
            worksheet.set_column(2, 2, 16)
            worksheet.set_column(3, 3, 20)
            worksheet.set_column(4, 4, 14)
            worksheet.set_column(5, 5, 16)
            worksheet.set_column(6, 6, 14)
            worksheet.set_column(7, 7, 10)
            worksheet.set_column(8, 8, 24)

            summary_row = len(records) + 1
            total_label_format = workbook.add_format({
                'bold': True,
                'align': 'right',
                'border': 1,
            })
            total_money_format = workbook.add_format({
                'bold': True,
                'align': 'right',
                'valign': 'vcenter',
                'border': 1,
                'num_format': '#,##0.00',
            })
            worksheet.write(summary_row, 5, 'Total:', total_label_format)
            worksheet.write(summary_row, 6, total_value, total_money_format)

            workbook.close()
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = 'xlsx'
        else:
            writer = csv.writer(io.TextIOWrapper(output, encoding='utf-8', newline=''))
            writer.writerow(headers)
            total_value = 0.0
            for rec in records:
                partner = rec.partner_id
                invoice_value = float(rec.invoice_value or 0.0)
                total_value += invoice_value
                writer.writerow([
                    partner.display_name or '',
                    partner.email or '',
                    partner.country_id.name or '',
                    rec.old_sales or '',
                    rec.invoice_date or '',
                    rec.invoice_number or '',
                    invoice_value,
                    rec.currency_id.name or '',
                    rec.lead_name or '',
                ])
            writer.writerow(['', '', '', '', '', 'Total:', total_value, '', ''])
            mimetype = 'text/csv'
            extension = 'csv'

        output.seek(0)
        file_name = f'Old_Sales_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{extension}'
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': mimetype,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
