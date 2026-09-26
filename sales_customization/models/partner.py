import logging
from datetime import date as py_date, datetime as py_datetime
from odoo import models, fields, api
from odoo.osv import expression
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    image_field_1 = fields.Image("Company Logo 1")
    port = fields.Char("Port")
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    old_sale_ids = fields.One2many(
        'crm.lead.old.sale',
        'partner_id',
        string='Old Sales',
    )
    old_sale_count = fields.Integer(
        string='Old Sales Count',
        compute='_compute_old_sales',
        store=False,
    )
    old_sale_total = fields.Monetary(
        string='Old Sales Total',
        currency_field='currency_id',
        compute='_compute_old_sales',
        store=False,
    )
    sale_order_count = fields.Integer(
        string='Sale Orders',
        compute='_compute_sale_orders',
        store=False,
    )
    sale_order_total = fields.Monetary(
        string='Sale Orders Total',
        currency_field='currency_id',
        compute='_compute_sale_orders',
        store=False,
    )
    last_sale_date = fields.Date(
        string='Last Sale Date',
        compute='_compute_sale_orders',
        store=False,
    )
    sale_invoice_count = fields.Integer(
        string='Sale Invoices',
        compute='_compute_sale_invoices',
        store=False,
    )
    sale_invoice_total = fields.Monetary(
        string='Sale Invoices Total',
        currency_field='currency_id',
        compute='_compute_sale_invoices',
        store=False,
    )
    last_invoice_date = fields.Date(
        string='Last Invoice Date',
        compute='_compute_sale_invoices',
        store=False,
    )
    invoice_ids = fields.One2many(
        'account.move',
        'partner_id',
        string='Sale Invoices',
        domain=[('move_type', 'in', ('out_invoice', 'out_refund'))],
    )
    user_ids = fields.Many2many(
        'res.users',
        'res_partner_user_rel',
        'partner_id',
        'user_id',
        string='Users',
        help='Additional users assigned to this partner.',
    )

    brand_id = fields.Many2one(
        'product.brand',
        string='Customer Brand',
    )
    # code = fields.Char("code")

    def action_custom_save(self):
        """ Custom save action """
        return True  # Odoo automatically saves records when an action is performed.

    @api.depends('old_sale_ids.invoice_value')
    def _compute_old_sales(self):
        for partner in self:
            total = sum(partner.old_sale_ids.mapped('invoice_value'))
            partner.old_sale_total = total
            partner.old_sale_count = len(partner.old_sale_ids)

    def _compute_sale_orders(self):
        SaleOrder = self.env['sale.order']
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
            ]
            data = SaleOrder.read_group(
                domain,
                ['amount_total:sum'],
                []
            )
            partner.sale_order_total = data[0].get('amount_total', 0.0) if data else 0.0
            partner.sale_order_count = SaleOrder.search_count(domain)
            last_order = SaleOrder.search(domain, order='date_order desc', limit=1)
            partner.last_sale_date = last_order.date_order.date() if last_order else False

    def _compute_sale_invoices(self):
        Move = self.env['account.move']
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '!=', 'cancel'),
            ]
            data = Move.read_group(
                domain,
                ['amount_total:sum'],
                []
            )
            partner.sale_invoice_total = data[0].get('amount_total', 0.0) if data else 0.0
            partner.sale_invoice_count = Move.search_count(domain)
            last_invoice = Move.search(domain, order='invoice_date desc, date desc', limit=1)
            partner.last_invoice_date = last_invoice.invoice_date or last_invoice.date or False

    def action_open_old_sales_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Old Sales Analysis',
            'res_model': 'crm.lead.old.sale',
            'view_mode': 'graph,pivot,tree',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'search_default_group_by_invoice_date': 1,
            },
        }

    def action_open_sale_orders_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Orders Analysis',
            'res_model': 'sale.order',
            'view_mode': 'graph,pivot,tree',
            'domain': [
                ('partner_id', '=', self.id),
                ('state', 'in', ['sale', 'done']),
            ],
            'context': {
                'search_default_groupby_date_order': 1,
            },
        }

    def action_open_sale_invoices_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Invoices Analysis',
            'res_model': 'account.move',
            'view_mode': 'graph,pivot,tree',
            'domain': [
                ('partner_id', '=', self.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '!=', 'cancel'),
            ],
            'context': {
                'search_default_groupby_invoice_date': 1,
            },
        }

    @api.model
    def get_sales_dashboard_search_view_id(self):
        """Resolve dashboard search view without requiring ir.model.data ACL."""
        data = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'sales_customization'),
            ('name', '=', 'view_sales_dashboard_search'),
            ('model', '=', 'ir.ui.view'),
        ], limit=1)
        return data.res_id if data else False

    def action_open_sales_dashboard(self):
        self.ensure_one()
        search_view_id = self.get_sales_dashboard_search_view_id()
        return {
            'type': 'ir.actions.client',
            'name': 'Sales Dashboard',
            'tag': 'sales_customization.sales_dashboard',
            'params': {
                'search_view_id': search_view_id,
            },
            'context': {
                'partner_id': self.id,
            },
        }

    @api.model
    def _sales_dashboard_months(self, months=12, start_date=None, end_date=None):
        if start_date or end_date:
            if not end_date:
                end_date = fields.Date.context_today(self)
            if not start_date:
                end = fields.Date.to_date(end_date).replace(day=1)
                start = (end - relativedelta(months=months - 1)).replace(day=1)
            else:
                start = fields.Date.to_date(start_date).replace(day=1)
                end = fields.Date.to_date(end_date).replace(day=1)
        else:
            end = fields.Date.context_today(self)
            start = (end - relativedelta(months=months - 1)).replace(day=1)
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current = current + relativedelta(months=1)
        labels = [d.strftime('%b %Y') for d in dates]
        keys = [d.strftime('%Y-%m') for d in dates]
        return start, end, labels, keys

    @api.model
    def _aggregate_by_month(self, model, domain, date_field, value_field, months=12, start_date=None, end_date=None):
        start, end, labels, keys = self._sales_dashboard_months(
            months=months,
            start_date=start_date,
            end_date=end_date,
        )
        domain = list(domain) + [
            (date_field, '>=', start),
            (date_field, '<=', end),
        ]
        data = model.read_group(
            domain,
            [f'{value_field}:sum'],
            [f'{date_field}:month'],
        )
        totals = {k: 0.0 for k in keys}
        counts = {k: 0 for k in keys}
        for row in data:
            month_value = row.get(f'{date_field}:month')
            month_date = False
            if month_value:
                if isinstance(month_value, (py_date, py_datetime)):
                    month_date = fields.Date.to_date(month_value)
                elif isinstance(month_value, str):
                    try:
                        month_date = fields.Date.to_date(month_value)
                    except Exception:
                        month_date = False
                    if not month_date:
                        for fmt in ('%B %Y', '%b %Y'):
                            try:
                                month_date = fields.Date.to_date(
                                    py_datetime.strptime(month_value, fmt).date()
                                )
                                break
                            except Exception:
                                month_date = False
            if not month_date:
                domain_hint = row.get('__domain') or []
                for item in domain_hint:
                    if (
                        isinstance(item, (list, tuple))
                        and len(item) >= 3
                        and item[0] == date_field
                        and item[1] == '>='
                    ):
                        try:
                            month_date = fields.Date.to_date(item[2])
                        except Exception:
                            month_date = False
                        break
            if not month_date:
                continue
            key = month_date.strftime('%Y-%m')
            totals[key] = row.get(value_field, row.get(f'{value_field}_sum', 0.0))
            counts[key] = row.get('__count', 0)
        total_series = [totals[k] for k in keys]
        count_series = [counts[k] for k in keys]
        return labels, total_series, count_series

    @api.model
    def _sales_dashboard_base_domains(self, partner_id=False, start_date=False, end_date=False, so_domain_extra=None):
        so_domain = list(so_domain_extra or [])
        has_state_filter = any(
            isinstance(leaf, (list, tuple)) and len(leaf) >= 3 and leaf[0] == 'state'
            for leaf in so_domain
        )
        if not has_state_filter:
            so_domain = (
                expression.AND([so_domain, [('state', 'in', ['sale', 'done'])]])
                if so_domain else [('state', 'in', ['sale', 'done'])]
            )
        inv_domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '!=', 'cancel'),
        ]
        old_domain = []
        if partner_id:
            so_domain.append(('partner_id', '=', partner_id))
            inv_domain.append(('partner_id', '=', partner_id))
            old_domain.append(('partner_id', '=', partner_id))
        filter_start = start_date
        filter_end = end_date
        if end_date and not start_date:
            end_dt = fields.Date.to_date(end_date)
            filter_start = (end_dt - relativedelta(months=11)).replace(day=1)
        if start_date and not end_date:
            filter_end = fields.Date.context_today(self)

        if filter_start:
            so_domain.append(('date_order', '>=', filter_start))
            inv_domain.append(('invoice_date', '>=', filter_start))
            old_domain.append(('invoice_date', '>=', filter_start))
        if filter_end:
            so_domain.append(('date_order', '<=', filter_end))
            inv_domain.append(('invoice_date', '<=', filter_end))
            old_domain.append(('invoice_date', '<=', filter_end))

        line_domain = [('order_id.state', 'in', ['sale', 'done'])]
        if partner_id:
            line_domain.append(('order_id.partner_id', '=', partner_id))
        if filter_start:
            line_domain.append(('order_id.date_order', '>=', filter_start))
        if filter_end:
            line_domain.append(('order_id.date_order', '<=', filter_end))

        return {
            'so_domain': so_domain,
            'inv_domain': inv_domain,
            'old_domain': old_domain,
            'line_domain': line_domain,
            'filter_start': filter_start,
            'filter_end': filter_end,
        }

    @api.model
    def get_sales_dashboard_data(self, partner_id=False, start_date=False, end_date=False, so_domain_extra=None):
        partner = self.browse(partner_id).exists() if partner_id else self.env['res.partner']
        currency = self.env.company.currency_id

        domains = self._sales_dashboard_base_domains(
            partner_id=partner_id,
            start_date=start_date,
            end_date=end_date,
            so_domain_extra=so_domain_extra,
        )
        so_domain = domains['so_domain']
        inv_domain = domains['inv_domain']
        old_domain = domains['old_domain']
        line_domain = domains['line_domain']
        filter_start = domains['filter_start']
        filter_end = domains['filter_end']

        so_total_data = self.env['sale.order'].read_group(so_domain, ['amount_total:sum'], [])
        so_total = so_total_data[0].get('amount_total', 0.0) if so_total_data else 0.0
        so_count = self.env['sale.order'].search_count(so_domain)
        last_order = self.env['sale.order'].search(so_domain, order='date_order desc', limit=1)

        inv_total_data = self.env['account.move'].read_group(inv_domain, ['amount_total:sum'], [])
        inv_total = inv_total_data[0].get('amount_total', 0.0) if inv_total_data else 0.0
        inv_count = self.env['account.move'].search_count(inv_domain)
        last_invoice = self.env['account.move'].search(inv_domain, order='invoice_date desc, date desc', limit=1)

        refund_domain = list(inv_domain) + [('move_type', '=', 'out_refund')]
        refund_total_data = self.env['account.move'].read_group(refund_domain, ['amount_total:sum'], [])
        refund_total = refund_total_data[0].get('amount_total', 0.0) if refund_total_data else 0.0
        refund_count = self.env['account.move'].search_count(refund_domain)

        old_total_data = self.env['crm.lead.old.sale'].read_group(old_domain, ['invoice_value:sum'], [])
        old_total = old_total_data[0].get('invoice_value', 0.0) if old_total_data else 0.0
        old_count = self.env['crm.lead.old.sale'].search_count(old_domain)

        labels, so_totals, so_counts = self._aggregate_by_month(
            self.env['sale.order'],
            so_domain,
            'date_order',
            'amount_total',
            start_date=filter_start,
            end_date=filter_end,
        )
        _, inv_totals, inv_counts = self._aggregate_by_month(
            self.env['account.move'],
            inv_domain,
            'invoice_date',
            'amount_total',
            start_date=filter_start,
            end_date=filter_end,
        )
        _, old_totals, old_counts = self._aggregate_by_month(
            self.env['crm.lead.old.sale'],
            old_domain,
            'invoice_date',
            'invoice_value',
            start_date=filter_start,
            end_date=filter_end,
        )

        paid_domain = list(inv_domain) + [('payment_state', '=', 'paid')]
        open_domain = list(inv_domain) + [('payment_state', 'in', ['not_paid', 'partial'])]
        paid_total_data = self.env['account.move'].read_group(paid_domain, ['amount_total:sum'], [])
        open_total_data = self.env['account.move'].read_group(open_domain, ['amount_residual:sum'], [])
        paid_total = paid_total_data[0].get('amount_total', 0.0) if paid_total_data else 0.0
        open_total = open_total_data[0].get('amount_residual', 0.0) if open_total_data else 0.0
        paid_pct = (paid_total / inv_total * 100.0) if inv_total else 0.0
        open_pct = (open_total / inv_total * 100.0) if inv_total else 0.0

        payment_state_data = self.env['account.move'].read_group(
            inv_domain,
            ['amount_total:sum'],
            ['payment_state'],
        )
        payment_states = []
        for row in payment_state_data:
            label = row.get('payment_state') or 'unknown'
            payment_states.append({
                'label': label,
                'value': row.get('amount_total', row.get('amount_total_sum', 0.0)),
            })

        top_customers = []
        if not partner_id:
            top_data = self.env['sale.order'].read_group(
                so_domain,
                ['amount_total:sum'],
                ['partner_id'],
                orderby='amount_total desc',
                limit=10,
            )
            for row in top_data:
                partner_val = row.get('partner_id')
                if not partner_val:
                    continue
                top_customers.append({
                    'id': partner_val[0],
                    'name': partner_val[1],
                    'total': row.get('amount_total', row.get('amount_total_sum', 0.0)),
                    'count': row.get('__count', 0),
                })

        top_customer_share = 0.0
        if top_customers and so_total:
            top_customer_share = sum(c['total'] for c in top_customers[:5]) / so_total * 100.0

        top_items = []
        top_item_data = self.env['sale.order.line'].read_group(
            line_domain + [('product_id', '!=', False)],
            ['price_total:sum'],
            ['product_id'],
            orderby='price_total desc',
            limit=10,
        )
        for row in top_item_data:
            product_val = row.get('product_id')
            if not product_val:
                continue
            top_items.append({
                'id': product_val[0],
                'name': product_val[1],
                'total': row.get('price_total', row.get('price_total_sum', 0.0)),
            })

        top_categories = []
        # read_group on product_id.categ_id can error on some setups; aggregate in Python for safety
        cat_totals = {}
        lines_for_cat = self.env['sale.order.line'].search(
            line_domain + [('product_id', '!=', False)],
            limit=5000,
            order='price_total desc',
        )
        for line in lines_for_cat:
            categ = line.product_id.categ_id
            if not categ:
                continue
            cat_totals.setdefault(categ.id, {'id': categ.id, 'name': categ.name, 'total': 0.0})
            cat_totals[categ.id]['total'] += line.price_total or 0.0
        top_categories = sorted(cat_totals.values(), key=lambda x: x['total'], reverse=True)[:10]

        container_types = []
        container_data = self.env['sale.order'].read_group(
            so_domain,
            ['amount_total:sum'],
            ['container_type'],
        )
        container_labels = {
            '20fcl': '20FCL',
            '40fcl': '40FCL',
            '45hc': '45HC',
            'lcl': 'LCL',
        }
        for row in container_data:
            key = row.get('container_type') or 'unknown'
            container_types.append({
                'key': key,
                'label': container_labels.get(key, key),
                'value': row.get('amount_total', row.get('amount_total_sum', 0.0)),
            })

        aging_buckets = {
            '0-30': 0.0,
            '31-60': 0.0,
            '61-90': 0.0,
            '90+': 0.0,
        }
        today = fields.Date.context_today(self)
        open_invoices = self.env['account.move'].search(
            open_domain,
            limit=2000,
            order='invoice_date_due asc, date asc',
        )
        for inv in open_invoices:
            due = inv.invoice_date_due or inv.invoice_date or inv.date
            if not due:
                aging_buckets['0-30'] += inv.amount_residual
                continue
            days = (today - due).days
            if days <= 30:
                aging_buckets['0-30'] += inv.amount_residual
            elif days <= 60:
                aging_buckets['31-60'] += inv.amount_residual
            elif days <= 90:
                aging_buckets['61-90'] += inv.amount_residual
            else:
                aging_buckets['90+'] += inv.amount_residual

        new_customers = 0
        returning_customers = 0
        if filter_start:
            first_sale_data = self.env['sale.order'].read_group(
                so_domain,
                ['date_order:min'],
                ['partner_id'],
            )
            for row in first_sale_data:
                first_date = row.get('date_order_min')
                if not first_date:
                    continue
                first_date = fields.Date.to_date(first_date)
                if first_date >= filter_start:
                    new_customers += 1
                else:
                    returning_customers += 1

        avg_days_to_invoice = 0.0
        invoiced_orders = self.env['sale.order'].search(
            so_domain + [('invoice_ids', '!=', False)],
            limit=2000,
            order='date_order desc',
        )
        total_days = 0
        count_days = 0
        for order in invoiced_orders:
            invoice_dates = order.invoice_ids.mapped('invoice_date')
            invoice_dates = [d for d in invoice_dates if d]
            if not invoice_dates:
                continue
            first_inv = min(invoice_dates)
            if order.date_order:
                total_days += (first_inv - order.date_order.date()).days
                count_days += 1
        if count_days:
            avg_days_to_invoice = total_days / count_days

        avg_days_to_pay = 0.0
        payment_model = self.env['account.payment']
        if 'reconciled_invoice_ids' in payment_model._fields:
            paid_invoices = self.env['account.move'].search(
                paid_domain,
                limit=2000,
                order='invoice_date desc, date desc',
            )
            total_pay_days = 0
            pay_count = 0
            for inv in paid_invoices:
                inv_date = inv.invoice_date or inv.date
                if not inv_date:
                    continue
                payments = payment_model.search(
                    [('reconciled_invoice_ids', 'in', inv.id)],
                    limit=10,
                    order='date asc',
                )
                if not payments:
                    continue
                pay_date = payments[0].date
                if pay_date:
                    total_pay_days += (pay_date - inv_date).days
                    pay_count += 1
            if pay_count:
                avg_days_to_pay = total_pay_days / pay_count

        paid_labels, paid_totals, _ = self._aggregate_by_month(
            self.env['account.move'],
            paid_domain,
            'invoice_date',
            'amount_total',
            start_date=filter_start,
            end_date=filter_end,
        )
        _, open_totals, _ = self._aggregate_by_month(
            self.env['account.move'],
            open_domain,
            'invoice_date',
            'amount_residual',
            start_date=filter_start,
            end_date=filter_end,
        )
        _, refund_totals, _ = self._aggregate_by_month(
            self.env['account.move'],
            refund_domain,
            'invoice_date',
            'amount_total',
            start_date=filter_start,
            end_date=filter_end,
        )

        sales_by_salesperson = []
        sp_data = self.env['sale.order'].read_group(
            so_domain,
            ['amount_total:sum'],
            ['user_id'],
            orderby='amount_total desc',
            limit=10,
        )
        for row in sp_data:
            user_val = row.get('user_id')
            if not user_val:
                continue
            sales_by_salesperson.append({
                'id': user_val[0],
                'name': user_val[1],
                'total': row.get('amount_total', row.get('amount_total_sum', 0.0)),
            })

        sales_by_country = []
        # read_group on partner_id.country_id can error on some setups; aggregate in Python for safety
        country_totals = {}
        orders_for_country = self.env['sale.order'].search(
            so_domain,
            limit=5000,
            order='amount_total desc',
        )
        for order in orders_for_country:
            country = order.partner_id.country_id
            if not country:
                continue
            country_totals.setdefault(country.id, {'id': country.id, 'name': country.name, 'total': 0.0})
            country_totals[country.id]['total'] += order.amount_total or 0.0
        sales_by_country = sorted(country_totals.values(), key=lambda x: x['total'], reverse=True)[:10]

        sales_by_port = []
        port_data = self.env['sale.order'].read_group(
            so_domain,
            ['amount_total:sum'],
            ['port_of_discharge'],
            orderby='amount_total desc',
            limit=10,
        )
        for row in port_data:
            port_val = row.get('port_of_discharge') or 'Unknown'
            sales_by_port.append({
                'name': port_val,
                'total': row.get('amount_total', row.get('amount_total_sum', 0.0)),
            })

        sales_by_brand = []
        if 'brand_id' in self.env['product.template']._fields:
            brand_totals = {}
            lines_for_brand = self.env['sale.order.line'].search(
                line_domain + [('product_id', '!=', False)],
                limit=5000,
                order='price_total desc',
            )
            for line in lines_for_brand:
                brand = line.product_id.product_tmpl_id.brand_id
                if not brand:
                    brand_totals.setdefault('none', {'id': False, 'name': 'No Brand', 'total': 0.0})
                    brand_totals['none']['total'] += line.price_total or 0.0
                    continue
                brand_totals.setdefault(brand.id, {'id': brand.id, 'name': brand.name, 'total': 0.0})
                brand_totals[brand.id]['total'] += line.price_total or 0.0
            sales_by_brand = sorted(brand_totals.values(), key=lambda x: x['total'], reverse=True)[:10]

        payment_terms = []
        term_data = self.env['account.move'].read_group(
            inv_domain,
            ['amount_total:sum'],
            ['invoice_payment_term_id'],
            orderby='amount_total desc',
            limit=10,
        )
        for row in term_data:
            term_val = row.get('invoice_payment_term_id')
            if not term_val:
                continue
            payment_terms.append({
                'id': term_val[0],
                'name': term_val[1],
                'total': row.get('amount_total', row.get('amount_total_sum', 0.0)),
            })

        margin_total = 0.0
        margin_pct = 0.0
        margin_series = []
        if 'margin' in self.env['sale.order.line']._fields:
            margin_data = self.env['sale.order.line'].read_group(
                line_domain,
                ['margin:sum', 'price_subtotal:sum'],
                [],
            )
            if margin_data:
                margin_total = margin_data[0].get('margin', 0.0)
                subtotal = margin_data[0].get('price_subtotal', 0.0) or 0.0
                margin_pct = (margin_total / subtotal * 100.0) if subtotal else 0.0
            _, margin_totals, _ = self._aggregate_by_month(
                self.env['sale.order.line'],
                line_domain,
                'order_id.date_order',
                'margin',
                start_date=filter_start,
                end_date=filter_end,
            )
            margin_series = margin_totals
        else:
            start, end, labels, keys = self._sales_dashboard_months(
                start_date=filter_start,
                end_date=filter_end,
            )
            margin_line_domain = list(line_domain) + [
                ('order_id.date_order', '>=', start),
                ('order_id.date_order', '<=', end),
            ]
            lines = self.env['sale.order.line'].search(margin_line_domain, limit=5000)
            subtotal = 0.0
            for line in lines:
                if 'purchase_price' in line._fields:
                    unit_cost = line.purchase_price or 0.0
                else:
                    unit_cost = line.product_id.standard_price or 0.0
                cost = unit_cost * (line.product_uom_qty or 0.0)
                margin_total += (line.price_subtotal or 0.0) - cost
                subtotal += line.price_subtotal or 0.0
            margin_pct = (margin_total / subtotal * 100.0) if subtotal else 0.0
            month_map = {k: 0.0 for k in keys}
            for line in lines:
                if not line.order_id.date_order:
                    continue
                key = line.order_id.date_order.strftime('%Y-%m')
                if key not in month_map:
                    continue
                if 'purchase_price' in line._fields:
                    unit_cost = line.purchase_price or 0.0
                else:
                    unit_cost = line.product_id.standard_price or 0.0
                cost = unit_cost * (line.product_uom_qty or 0.0)
                month_map[key] += (line.price_subtotal or 0.0) - cost
            margin_series = [month_map[k] for k in keys]

        cohort_new = []
        cohort_returning = []
        if filter_start:
            start, end, labels, keys = self._sales_dashboard_months(
                start_date=filter_start,
                end_date=filter_end,
            )
            first_sale_data = self.env['sale.order'].read_group(
                so_domain,
                ['date_order:min'],
                ['partner_id'],
            )
            first_sale_map = {}
            for row in first_sale_data:
                pid = row.get('partner_id')
                if not pid:
                    continue
                first_sale_map[pid[0]] = fields.Date.to_date(row.get('date_order_min'))

            for key in keys:
                month_date = fields.Date.to_date(f"{key}-01")
                month_start = month_date
                month_end = (month_date + relativedelta(months=1)) - relativedelta(days=1)
                month_domain = list(so_domain) + [
                    ('date_order', '>=', month_start),
                    ('date_order', '<=', month_end),
                ]
                month_partners = self.env['sale.order'].read_group(
                    month_domain,
                    ['partner_id'],
                    ['partner_id'],
                )
                new_count = 0
                ret_count = 0
                for row in month_partners:
                    pid = row.get('partner_id')
                    if not pid:
                        continue
                    first_date = first_sale_map.get(pid[0])
                    if not first_date:
                        continue
                    if first_date >= month_start and first_date <= month_end:
                        new_count += 1
                    else:
                        ret_count += 1
                cohort_new.append(new_count)
                cohort_returning.append(ret_count)

        _, _, _, month_keys = self._sales_dashboard_months(
            start_date=filter_start,
            end_date=filter_end,
        )

        return {
            'partner': {
                'id': partner.id if partner_id else False,
                'name': partner.name if partner_id else False,
            },
            'currency': {
                'symbol': currency.symbol,
                'position': currency.position,
            },
            'kpis': {
                'sale_order_total': so_total,
                'sale_order_count': so_count,
                'last_sale_date': last_order.date_order.date() if last_order else False,
                'sale_invoice_total': inv_total,
                'sale_invoice_count': inv_count,
                'last_invoice_date': last_invoice.invoice_date or last_invoice.date or False,
                'old_sale_total': old_total,
                'old_sale_count': old_count,
                'invoice_paid_total': paid_total,
                'invoice_open_total': open_total,
                'avg_order_value': (so_total / so_count) if so_count else 0.0,
                'avg_invoice_value': (inv_total / inv_count) if inv_count else 0.0,
                'refund_total': refund_total,
                'refund_count': refund_count,
                'refund_pct': (refund_total / inv_total * 100.0) if inv_total else 0.0,
                'paid_pct': paid_pct,
                'open_pct': open_pct,
                'top_customer_share': top_customer_share,
                'new_customers': new_customers,
                'returning_customers': returning_customers,
                'avg_days_to_invoice': avg_days_to_invoice,
                'avg_days_to_pay': avg_days_to_pay,
                'margin_total': margin_total,
                'margin_pct': margin_pct,
            },
            'labels': labels,
            'month_keys': month_keys,
            'series': {
                'sale_orders': {
                    'total': so_totals,
                    'count': so_counts,
                },
                'sale_invoices': {
                    'total': inv_totals,
                    'count': inv_counts,
                },
                'old_sales': {
                    'total': old_totals,
                    'count': old_counts,
                },
                'paid_open': {
                    'labels': paid_labels,
                    'paid': paid_totals,
                    'open': open_totals,
                },
                'refunds': {
                    'labels': paid_labels,
                    'total': refund_totals,
                },
                'margin': {
                    'labels': paid_labels,
                    'total': margin_series,
                },
                'cohort': {
                    'labels': paid_labels,
                    'new': cohort_new,
                    'returning': cohort_returning,
                },
            },
            'payment_states': payment_states,
            'top_customers': top_customers,
            'top_items': top_items,
            'top_categories': top_categories,
            'container_types': container_types,
            'aging_buckets': aging_buckets,
            'sales_by_salesperson': sales_by_salesperson,
            'sales_by_brand': sales_by_brand,
            'sales_by_country': sales_by_country,
            'sales_by_port': sales_by_port,
            'payment_terms': payment_terms,
        }

    def _dashboard_month_bounds(self, month_key):
        start = fields.Date.to_date(f"{month_key}-01")
        end = start + relativedelta(months=1, days=-1)
        return start, end

    def _dashboard_json_domain(self, domain):
        result = []
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and len(leaf) >= 3:
                val = leaf[2]
                if isinstance(val, py_datetime):
                    val = fields.Datetime.to_string(val)
                elif isinstance(val, py_date):
                    val = fields.Date.to_string(val)
                result.append([leaf[0], leaf[1], val])
            else:
                result.append(leaf)
        return result

    def _dashboard_with_month(self, domain, date_field, month_key):
        domain = list(domain)
        if not month_key:
            return domain
        start, end = self._dashboard_month_bounds(month_key)
        return domain + [(date_field, '>=', start), (date_field, '<=', end)]

    def _dashboard_sum(self, model, domain, field_name):
        grouped = model.read_group(domain, [f'{field_name}:sum'], [])
        if not grouped:
            return 0.0
        return grouped[0].get(field_name, grouped[0].get(f'{field_name}_sum', 0.0)) or 0.0

    def _dashboard_detail_rows(self, records, name_get, date_get, amount_get, partner_get=None, extra_get=None):
        rows = []
        for rec in records:
            date_val = date_get(rec) if date_get else False
            if hasattr(date_val, 'strftime'):
                date_val = date_val.strftime('%Y-%m-%d')
            partner_name = ''
            if partner_get:
                partner_name = partner_get(rec) or ''
            rows.append({
                'id': rec.id,
                'name': name_get(rec) if name_get else str(rec.id),
                'date': date_val or '',
                'partner': partner_name,
                'amount': amount_get(rec) if amount_get else 0.0,
                'extra': extra_get(rec) if extra_get else '',
            })
        return rows

    def _dashboard_detail_payload(self, title, explanation, model, domain, records, count, amount,
                                  name_get, date_get, amount_get, partner_get=None, extra_get=None,
                                  amount_label='Total Amount', count_label='Records'):
        rows = self._dashboard_detail_rows(
            records, name_get, date_get, amount_get, partner_get, extra_get
        )
        return {
            'title': title,
            'explanation': explanation,
            'model': model,
            'domain': self._dashboard_json_domain(domain),
            'count': count,
            'amount': amount or 0.0,
            'amount_label': amount_label,
            'count_label': count_label,
            'rows': rows,
            'truncated': count > len(rows),
            'shown': len(rows),
        }

    def _dashboard_so_detail(self, domain, title, explanation, limit=80):
        orders = self.env['sale.order'].search(domain, limit=limit, order='date_order desc, id desc')
        return self._dashboard_detail_payload(
            title, explanation, 'sale.order', domain, orders,
            self.env['sale.order'].search_count(domain),
            self._dashboard_sum(self.env['sale.order'], domain, 'amount_total'),
            lambda r: r.name,
            lambda r: r.date_order,
            lambda r: r.amount_total or 0.0,
            lambda r: r.partner_id.display_name,
            lambda r: r.state,
            count_label='Orders',
        )

    def _dashboard_inv_detail(self, domain, title, explanation, amount_field='amount_total', limit=80):
        invoices = self.env['account.move'].search(
            domain, limit=limit, order='invoice_date desc, date desc, id desc'
        )
        return self._dashboard_detail_payload(
            title, explanation, 'account.move', domain, invoices,
            self.env['account.move'].search_count(domain),
            self._dashboard_sum(self.env['account.move'], domain, amount_field),
            lambda r: r.name,
            lambda r: r.invoice_date or r.date,
            lambda r: getattr(r, amount_field, 0.0) or 0.0,
            lambda r: r.partner_id.display_name,
            lambda r: r.payment_state,
            count_label='Invoices',
        )

    def _dashboard_old_detail(self, domain, title, explanation, limit=80):
        rows = self.env['crm.lead.old.sale'].search(domain, limit=limit, order='invoice_date desc, id desc')
        return self._dashboard_detail_payload(
            title, explanation, 'crm.lead.old.sale', domain, rows,
            self.env['crm.lead.old.sale'].search_count(domain),
            self._dashboard_sum(self.env['crm.lead.old.sale'], domain, 'invoice_value'),
            lambda r: r.invoice_number or r.old_sales or r.lead_name or f'#{r.id}',
            lambda r: r.invoice_date,
            lambda r: r.invoice_value or 0.0,
            lambda r: r.partner_id.display_name,
            count_label='Old Sales',
        )

    def _dashboard_line_detail(self, domain, title, explanation, amount_field='price_total', limit=80):
        lines = self.env['sale.order.line'].search(domain, limit=limit, order='id desc')

        def _line_amount(line):
            if amount_field == 'margin':
                if 'margin' in line._fields:
                    return line.margin or 0.0
                unit_cost = line.purchase_price if 'purchase_price' in line._fields else (
                    line.product_id.standard_price or 0.0
                )
                return (line.price_subtotal or 0.0) - (unit_cost * (line.product_uom_qty or 0.0))
            return getattr(line, amount_field, 0.0) or 0.0

        if amount_field == 'margin' and 'margin' not in self.env['sale.order.line']._fields:
            amount = sum(_line_amount(line) for line in self.env['sale.order.line'].search(domain, limit=5000))
        else:
            amount = self._dashboard_sum(self.env['sale.order.line'], domain, amount_field)

        return self._dashboard_detail_payload(
            title, explanation, 'sale.order.line', domain, lines,
            self.env['sale.order.line'].search_count(domain),
            amount,
            lambda r: r.product_id.display_name or r.name,
            lambda r: r.order_id.date_order,
            _line_amount,
            lambda r: r.order_id.partner_id.display_name,
            lambda r: r.order_id.name,
            amount_label='Line Amount' if amount_field != 'margin' else 'Margin',
            count_label='Order Lines',
        )

    def _dashboard_partner_ids_by_cohort(self, so_domain, filter_start, series_name, month_key=None):
        first_sale_data = self.env['sale.order'].read_group(
            so_domain,
            ['date_order:min'],
            ['partner_id'],
        )
        first_sale_map = {}
        for row in first_sale_data:
            partner_val = row.get('partner_id')
            first_date = row.get('date_order_min')
            if not partner_val or not first_date:
                continue
            first_sale_map[partner_val[0]] = fields.Date.to_date(first_date)

        partner_ids = []
        if month_key:
            month_start, month_end = self._dashboard_month_bounds(month_key)
            month_domain = self._dashboard_with_month(so_domain, 'date_order', month_key)
            month_partners = self.env['sale.order'].read_group(
                month_domain, ['partner_id'], ['partner_id']
            )
            for row in month_partners:
                partner_val = row.get('partner_id')
                if not partner_val:
                    continue
                first_date = first_sale_map.get(partner_val[0])
                if not first_date:
                    continue
                is_new = month_start <= first_date <= month_end
                if (series_name == 'new' and is_new) or (series_name != 'new' and not is_new):
                    partner_ids.append(partner_val[0])
            return partner_ids, month_domain

        if not filter_start:
            return [], so_domain
        for partner_id, first_date in first_sale_map.items():
            is_new = first_date >= filter_start
            if (series_name == 'new' and is_new) or (series_name != 'new' and not is_new):
                partner_ids.append(partner_id)
        return partner_ids, so_domain

    @api.model
    def get_sales_dashboard_details(
        self, chart_key, point=None, partner_id=False, start_date=False, end_date=False, so_domain_extra=None
    ):
        """Return source records and explanation for a dashboard KPI or chart point."""
        point = point or {}
        domains = self._sales_dashboard_base_domains(
            partner_id=partner_id,
            start_date=start_date,
            end_date=end_date,
            so_domain_extra=so_domain_extra,
        )
        so_domain = domains['so_domain']
        inv_domain = domains['inv_domain']
        old_domain = domains['old_domain']
        line_domain = domains['line_domain']
        filter_start = domains['filter_start']
        paid_domain = list(inv_domain) + [('payment_state', '=', 'paid')]
        open_domain = list(inv_domain) + [('payment_state', 'in', ['not_paid', 'partial'])]
        refund_domain = list(inv_domain) + [('move_type', '=', 'out_refund')]
        month_key = point.get('month_key') or False
        label = point.get('label') or point.get('name') or ''
        series_name = point.get('series_name') or ''
        record_id = point.get('id') or False
        record_key = point.get('key') or False
        period = f' — {label}' if label else ''

        if chart_key in ('sale_orders', 'kpi_sale_orders'):
            domain = self._dashboard_with_month(so_domain, 'date_order', month_key)
            return self._dashboard_so_detail(
                domain,
                f'Sales Orders{period}',
                'Confirmed sales orders in the selected filters. Amount is the sum of order totals. Count is the number of orders.',
            )

        if chart_key in ('sale_invoices', 'kpi_sale_invoices'):
            domain = self._dashboard_with_month(inv_domain, 'invoice_date', month_key)
            return self._dashboard_inv_detail(
                domain,
                f'Sales Invoices{period}',
                'Customer invoices and credit notes that are not cancelled. Amount is the sum of invoice totals.',
            )

        if chart_key in ('old_sales', 'kpi_old_sales'):
            domain = self._dashboard_with_month(old_domain, 'invoice_date', month_key)
            return self._dashboard_old_detail(
                domain,
                f'Historical (Old) Sales{period}',
                'Imported historical sales rows (Old Sales) in the selected period. Amount is the sum of invoice values.',
            )

        if chart_key in ('paid', 'kpi_paid', 'kpi_paid_pct'):
            domain = self._dashboard_with_month(paid_domain, 'invoice_date', month_key)
            explanation = (
                'Invoices whose payment state is Paid. Paid % = paid invoice total / all invoice total.'
                if chart_key == 'kpi_paid_pct'
                else 'Invoices whose payment state is Paid. Amount is the sum of those invoice totals.'
            )
            return self._dashboard_inv_detail(domain, f'Paid Invoices{period}', explanation)

        if chart_key in ('open', 'kpi_open', 'kpi_open_pct'):
            domain = self._dashboard_with_month(open_domain, 'invoice_date', month_key)
            explanation = (
                'Invoices that are Not Paid or Partially Paid. Open % uses outstanding residual / all invoice total.'
                if chart_key == 'kpi_open_pct'
                else 'Invoices that are Not Paid or Partially Paid. Amount is the outstanding residual.'
            )
            return self._dashboard_inv_detail(
                domain, f'Open Invoices{period}', explanation, amount_field='amount_residual'
            )

        if chart_key in ('refunds', 'kpi_refund_total', 'kpi_refund_count', 'kpi_refund_pct'):
            domain = self._dashboard_with_month(refund_domain, 'invoice_date', month_key)
            explanation = (
                'Customer credit notes (out_refund). Returns Impact % = credit note total / all invoice total.'
                if chart_key == 'kpi_refund_pct'
                else 'Customer credit notes (out_refund). Amount is the sum of credit note totals.'
            )
            return self._dashboard_inv_detail(domain, f'Credit Notes{period}', explanation)

        if chart_key in ('kpi_avg_order',):
            return self._dashboard_so_detail(
                so_domain,
                'Average Order Value',
                'Average Order Value = total of confirmed sales orders / number of those orders.',
            )

        if chart_key in ('kpi_avg_invoice',):
            return self._dashboard_inv_detail(
                inv_domain,
                'Average Invoice Value',
                'Average Invoice Value = total of customer invoices and credit notes / number of those invoices.',
            )

        if chart_key == 'payment_states':
            state = record_key or label or 'unknown'
            domain = list(inv_domain)
            if state == 'unknown':
                domain.append(('payment_state', 'in', [False, '']))
            else:
                domain.append(('payment_state', '=', state))
            return self._dashboard_inv_detail(
                domain,
                f'Invoices — {state}',
                'Customer invoices grouped by payment state. The slice amount is the sum of invoice totals in that state.',
            )

        if chart_key == 'top_customers':
            domain = list(so_domain)
            if record_id:
                domain.append(('partner_id', '=', record_id))
            return self._dashboard_so_detail(
                domain,
                f'Top Customer{period}',
                'Confirmed sales orders for this customer. The bar amount is the sum of those order totals.',
            )

        if chart_key == 'top_items':
            domain = list(line_domain) + [('product_id', '!=', False)]
            if record_id:
                domain.append(('product_id', '=', record_id))
            return self._dashboard_line_detail(
                domain,
                f'Top Item{period}',
                'Sale order lines for this product on confirmed orders. The bar amount is the sum of line totals.',
            )

        if chart_key == 'top_categories':
            domain = list(line_domain) + [('product_id', '!=', False)]
            if record_id:
                domain.append(('product_id.categ_id', '=', record_id))
            return self._dashboard_line_detail(
                domain,
                f'Top Category{period}',
                'Sale order lines whose product belongs to this category. The bar amount is the sum of line totals.',
            )

        if chart_key == 'container_types':
            key = record_key or 'unknown'
            domain = list(so_domain)
            if key == 'unknown':
                domain.append(('container_type', 'in', [False, '']))
            else:
                domain.append(('container_type', '=', key))
            return self._dashboard_so_detail(
                domain,
                f'Container Type — {label or key}',
                'Confirmed sales orders with this container type. The slice amount is the sum of order totals.',
            )

        if chart_key == 'aging':
            today = fields.Date.context_today(self)
            bucket = record_key or label or '0-30'
            open_invoices = self.env['account.move'].search(
                open_domain, limit=2000, order='invoice_date_due asc, date asc'
            )
            matching_ids = []
            for inv in open_invoices:
                due = inv.invoice_date_due or inv.invoice_date or inv.date
                if not due:
                    inv_bucket = '0-30'
                else:
                    days = (today - due).days
                    if days <= 30:
                        inv_bucket = '0-30'
                    elif days <= 60:
                        inv_bucket = '31-60'
                    elif days <= 90:
                        inv_bucket = '61-90'
                    else:
                        inv_bucket = '90+'
                if inv_bucket == bucket:
                    matching_ids.append(inv.id)
            domain = [('id', 'in', matching_ids)]
            return self._dashboard_inv_detail(
                domain,
                f'Invoice Aging — {bucket} days',
                'Open invoices (not paid / partial) grouped by days past due. Amount is the outstanding residual. '
                '0-30 also includes invoices that are not yet due or have no due date.',
                amount_field='amount_residual',
            )

        if chart_key == 'paid_open':
            base = paid_domain if series_name != 'open' else open_domain
            amount_field = 'amount_total' if series_name != 'open' else 'amount_residual'
            domain = self._dashboard_with_month(base, 'invoice_date', month_key)
            title = f'{"Paid" if series_name != "open" else "Open"} Invoices{period}'
            explanation = (
                'Monthly paid invoices. Amount is the sum of paid invoice totals.'
                if series_name != 'open'
                else 'Monthly open invoices. Amount is the outstanding residual.'
            )
            return self._dashboard_inv_detail(domain, title, explanation, amount_field=amount_field)

        if chart_key in ('margin', 'kpi_margin'):
            domain = self._dashboard_with_month(line_domain, 'order_id.date_order', month_key)
            return self._dashboard_line_detail(
                domain,
                f'Gross Margin{period}',
                'Gross margin from confirmed sale order lines. Margin = sales subtotal minus cost. '
                'Margin % = margin / subtotal.',
                amount_field='margin',
            )

        if chart_key in ('cohort', 'kpi_new_customers', 'kpi_returning_customers'):
            series = series_name or ('new' if chart_key == 'kpi_new_customers' else 'returning')
            partner_ids, base_domain = self._dashboard_partner_ids_by_cohort(
                so_domain, filter_start, series, month_key=month_key if chart_key == 'cohort' else None
            )
            domain = list(base_domain) + [('partner_id', 'in', partner_ids or [0])]
            title = f'{"New" if series == "new" else "Returning"} Customers{period}'
            explanation = (
                'New customers are partners whose first confirmed order in the filtered period falls in this month. '
                if series == 'new'
                else 'Returning customers already had a confirmed order earlier in the filtered period. '
            ) + 'The list shows their orders that contribute to this value.'
            return self._dashboard_so_detail(domain, title, explanation)

        if chart_key == 'salesperson':
            domain = list(so_domain)
            if record_id:
                domain.append(('user_id', '=', record_id))
            return self._dashboard_so_detail(
                domain,
                f'Salesperson{period}',
                'Confirmed sales orders assigned to this salesperson. The bar amount is the sum of order totals.',
            )

        if chart_key == 'brand':
            domain = list(line_domain) + [('product_id', '!=', False)]
            if record_id:
                domain.append(('product_id.product_tmpl_id.brand_id', '=', record_id))
            elif record_id is False and (label == 'No Brand' or not label):
                domain.append(('product_id.product_tmpl_id.brand_id', '=', False))
            return self._dashboard_line_detail(
                domain,
                f'Brand{period}',
                'Sale order lines whose product has this brand. The bar amount is the sum of line totals.',
            )

        if chart_key == 'country':
            domain = list(so_domain)
            if record_id:
                domain.append(('partner_id.country_id', '=', record_id))
            return self._dashboard_so_detail(
                domain,
                f'Country{period}',
                'Confirmed sales orders whose customer is in this country. The bar amount is the sum of order totals.',
            )

        if chart_key == 'port':
            domain = list(so_domain)
            port_name = label or point.get('name')
            if port_name and port_name != 'Unknown':
                domain.append(('port_of_discharge', '=', port_name))
            else:
                domain.append(('port_of_discharge', 'in', [False, '']))
            return self._dashboard_so_detail(
                domain,
                f'Port{period}',
                'Confirmed sales orders with this port of discharge. The bar amount is the sum of order totals.',
            )

        if chart_key == 'payment_terms':
            domain = list(inv_domain)
            if record_id:
                domain.append(('invoice_payment_term_id', '=', record_id))
            return self._dashboard_inv_detail(
                domain,
                f'Payment Terms{period}',
                'Customer invoices using this payment term. The bar amount is the sum of invoice totals.',
            )

        if chart_key == 'kpi_top_customer_share':
            top_data = self.env['sale.order'].read_group(
                so_domain,
                ['amount_total:sum'],
                ['partner_id'],
                orderby='amount_total desc',
                limit=5,
            )
            partner_ids = [row['partner_id'][0] for row in top_data if row.get('partner_id')]
            domain = list(so_domain) + [('partner_id', 'in', partner_ids or [0])]
            return self._dashboard_so_detail(
                domain,
                'Top 5 Customer Share',
                'Share = total of the top 5 customers’ confirmed orders / total of all confirmed orders in the filters.',
            )

        if chart_key == 'kpi_avg_days_to_invoice':
            domain = list(so_domain) + [('invoice_ids', '!=', False)]
            orders = self.env['sale.order'].search(domain, limit=80, order='date_order desc')

            def _days(order):
                invoice_dates = [d for d in order.invoice_ids.mapped('invoice_date') if d]
                if not invoice_dates or not order.date_order:
                    return ''
                return f'{(min(invoice_dates) - order.date_order.date()).days} days'

            return self._dashboard_detail_payload(
                'Average Days to Invoice',
                'Average of (first invoice date − order date) for confirmed orders that have at least one invoice.',
                'sale.order',
                domain,
                orders,
                self.env['sale.order'].search_count(domain),
                0.0,
                lambda r: r.name,
                lambda r: r.date_order,
                lambda r: r.amount_total or 0.0,
                lambda r: r.partner_id.display_name,
                _days,
                amount_label='Order Total',
                count_label='Invoiced Orders',
            )

        if chart_key == 'kpi_avg_days_to_pay':
            invoices = self.env['account.move'].search(
                paid_domain, limit=80, order='invoice_date desc, date desc'
            )
            payment_model = self.env['account.payment']

            def _pay_days(inv):
                inv_date = inv.invoice_date or inv.date
                if not inv_date or 'reconciled_invoice_ids' not in payment_model._fields:
                    return ''
                payments = payment_model.search(
                    [('reconciled_invoice_ids', 'in', inv.id)], limit=1, order='date asc'
                )
                if not payments or not payments[0].date:
                    return ''
                return f'{(payments[0].date - inv_date).days} days'

            return self._dashboard_detail_payload(
                'Average Days to Pay',
                'Average of (first payment date − invoice date) for paid customer invoices.',
                'account.move',
                paid_domain,
                invoices,
                self.env['account.move'].search_count(paid_domain),
                self._dashboard_sum(self.env['account.move'], paid_domain, 'amount_total'),
                lambda r: r.name,
                lambda r: r.invoice_date or r.date,
                lambda r: r.amount_total or 0.0,
                lambda r: r.partner_id.display_name,
                _pay_days,
                count_label='Paid Invoices',
            )

        return {
            'title': 'Details',
            'explanation': 'No source records are available for this selection.',
            'model': False,
            'domain': [],
            'count': 0,
            'amount': 0.0,
            'amount_label': 'Total Amount',
            'count_label': 'Records',
            'rows': [],
            'truncated': False,
            'shown': 0,
        }

    def _resolve_company_for_property_accounts(self):
        """Company used for receivable/payable defaults (UI company first, then partner.company_id)."""
        company = self.env.company
        if company:
            return company
        if len(self) == 1 and self.company_id:
            return self.company_id
        return self.env['res.company'].browse()

    def _account_from_ir_default(self, company, field_name):
        """Optional user-defined defaults (Settings → Technical → Defaults)."""
        if not company:
            return self.env['account.account']
        raw = self.env['ir.default'].sudo()._get(
            'res.partner', field_name, user_id=False, company_id=company.id)
        if raw in (None, False):
            return self.env['account.account']
        aid = raw[0] if isinstance(raw, (list, tuple)) else raw
        try:
            aid = int(aid)
        except (TypeError, ValueError):
            return self.env['account.account']
        acc = self.env['account.account'].sudo().browse(aid)
        return acc if acc.exists() else self.env['account.account']

    def _get_default_account_receivable(self, company):
        """First receivable account for the company CoA; fallback ir.property / ir.default."""
        Account = self.env['account.account'].sudo().with_company(company)
        if not company:
            return Account.browse()
        acc = Account.search([
            ('company_id', '=', company.id),
            ('account_type', '=', 'asset_receivable'),
            ('deprecated', '=', False),
        ], limit=1, order='code')
        if acc:
            return acc
        prop = self.env['ir.property'].sudo().with_company(company)._get(
            'property_account_receivable_id', 'res.partner')
        if prop and prop._name == 'account.account':
            return prop
        acc = self._account_from_ir_default(company, 'property_account_receivable_id')
        if acc:
            return acc
        _logger.warning(
            'Partner autofill: no receivable account for company "%s" (id=%s). '
            'Install a chart of accounts or set Accounting default accounts for contacts.',
            company.name, company.id)
        return Account.browse()

    def _get_default_account_payable(self, company):
        Account = self.env['account.account'].sudo().with_company(company)
        if not company:
            return Account.browse()
        acc = Account.search([
            ('company_id', '=', company.id),
            ('account_type', '=', 'liability_payable'),
            ('deprecated', '=', False),
        ], limit=1, order='code')
        if acc:
            return acc
        prop = self.env['ir.property'].sudo().with_company(company)._get(
            'property_account_payable_id', 'res.partner')
        if prop and prop._name == 'account.account':
            return prop
        acc = self._account_from_ir_default(company, 'property_account_payable_id')
        if acc:
            return acc
        _logger.warning(
            'Partner autofill: no payable account for company "%s" (id=%s). '
            'Install a chart of accounts or set Accounting default accounts for contacts.',
            company.name, company.id)
        return Account.browse()

    def _merge_default_property_accounts_for_write(self, vals):
        """Inject default receivable/payable before write(); required-field validation runs inside write()."""
        if 'property_account_receivable_id' not in self._fields:
            return
        company = self._resolve_company_for_property_accounts()
        if not company:
            _logger.warning('Partner autofill: no company (env.company empty and partner has no company_id).')
            return
        rec_field = 'property_account_receivable_id'
        pay_field = 'property_account_payable_id'
        # Web client sends cleared m2o as key present + False — must treat like "missing".
        # Batch-safe: only set when every record is missing that property for this company.
        if not vals.get(rec_field):
            if all(not p.with_company(company).property_account_receivable_id for p in self):
                acc = self._get_default_account_receivable(company)
                if acc:
                    vals[rec_field] = acc.id
        if not vals.get(pay_field):
            if all(not p.with_company(company).property_account_payable_id for p in self):
                acc = self._get_default_account_payable(company)
                if acc:
                    vals[pay_field] = acc.id

    @api.model
    def _apply_default_property_accounts_to_vals(self, vals):
        if 'property_account_receivable_id' not in self._fields:
            return
        if vals.get('property_account_receivable_id') and vals.get('property_account_payable_id'):
            return
        company_id = vals.get('company_id')
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        if not company:
            return
        if not vals.get('property_account_receivable_id'):
            acc = self._get_default_account_receivable(company)
            if acc:
                vals['property_account_receivable_id'] = acc.id
        if not vals.get('property_account_payable_id'):
            acc = self._get_default_account_payable(company)
            if acc:
                vals['property_account_payable_id'] = acc.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'property_account_receivable_id' not in self._fields:
            return res
        company = self.env.company
        if not company and self.env.context.get('default_company_id'):
            company = self.env['res.company'].browse(self.env.context['default_company_id'])
        if not company:
            return res
        if 'property_account_receivable_id' in fields_list and not res.get('property_account_receivable_id'):
            acc = self._get_default_account_receivable(company)
            if acc:
                res['property_account_receivable_id'] = acc.id
        if 'property_account_payable_id' in fields_list and not res.get('property_account_payable_id'):
            acc = self._get_default_account_payable(company)
            if acc:
                res['property_account_payable_id'] = acc.id
        return res

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].title()
                vals['ref'] = ''.join(word[0] for word in vals['name'].split())
            self._apply_default_property_accounts_to_vals(vals)
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        self._merge_default_property_accounts_for_write(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].title()
            vals['ref'] = ''.join(word[0] for word in vals['name'].split())
        return super(ResPartner, self).write(vals)

