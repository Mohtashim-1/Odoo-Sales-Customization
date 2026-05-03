from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
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
    old_sale_invoice_total = fields.Monetary(
        string='Total invoice value',
        compute='_compute_old_sale_invoice_total',
        currency_field='company_currency',
    )

    @api.depends('old_sale_ids.invoice_value')
    def _compute_old_sale_invoice_total(self):
        for lead in self:
            lead.old_sale_invoice_total = sum(lead.old_sale_ids.mapped('invoice_value'))

    total_sales_orders_html = fields.Html(
        string='Total Sales Orders',
        compute='_compute_old_sales_dashboard_html',
        sanitize=False,
    )

    def _compute_old_sales_dashboard_html(self):
        def _fmt_money(amount, symbol):
            return f"{symbol} {amount:,.2f}"

        def _fmt_pct(value):
            return f"{value:+.1f}%"

        def _month_axis():
            today = fields.Date.today()
            first_day = today.replace(day=1)
            return [first_day - relativedelta(months=i) for i in range(11, -1, -1)]

        def _color_palette():
            return ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16"]

        for lead in self:
            total_orders = 0
            total_value = 0.0
            avg_order_value = 0.0
            last_order_date = '-'
            this_month_orders = 0
            old_sales_count = len(lead.old_sale_ids)
            old_sales_total = sum(lead.old_sale_ids.mapped('invoice_value'))
            prev_month_orders = 0
            prev_month_value = 0.0
            this_month_value = 0.0
            growth_orders_pct = 0.0
            growth_value_pct = 0.0
            best_month_label = '-'
            best_month_value = 0.0
            old_vs_order_ratio = 0.0
            top_products_html = ""
            top_categories_html = ""
            company_split_html = ""
            salesperson_split_html = ""
            product_mix_html = ""
            recency_bucket = "No order yet"
            avg_days_between_orders = 0.0
            conversion_days = 0
            first_order_date = "-"

            month_points = _month_axis()
            month_totals = {month.strftime('%b %y'): 0.0 for month in month_points}
            month_order_counts = {month.strftime('%b %y'): 0 for month in month_points}
            this_month_start = month_points[-1]
            next_month_start = this_month_start + relativedelta(months=1)
            prev_month_start = this_month_start - relativedelta(months=1)

            if lead.partner_id:
                partner = lead.partner_id.commercial_partner_id
                order_domain = [
                    ('partner_id', 'child_of', partner.id),
                    ('state', 'not in', ['cancel']),
                ]
                orders = self.env['sale.order'].search(order_domain, order='date_order desc')
                total_orders = len(orders)
                total_value = sum(orders.mapped('amount_total'))
                avg_order_value = total_value / total_orders if total_orders else 0.0
                if orders:
                    last_date = orders[0].date_order
                    last_order_date = fields.Date.to_date(last_date).strftime('%d-%m-%Y') if last_date else '-'
                    first_date = orders[-1].date_order
                    if first_date:
                        first_order = fields.Date.to_date(first_date)
                        first_order_date = first_order.strftime('%d-%m-%Y')
                        if lead.create_date:
                            lead_date = fields.Date.to_date(lead.create_date)
                            conversion_days = (first_order - lead_date).days

                this_month_orders = len(
                    orders.filtered(
                        lambda o: o.date_order and this_month_start <= fields.Date.to_date(o.date_order) < next_month_start
                    )
                )
                prev_month_orders = len(
                    orders.filtered(
                        lambda o: o.date_order and prev_month_start <= fields.Date.to_date(o.date_order) < this_month_start
                    )
                )

                for order in orders:
                    if not order.date_order:
                        continue
                    order_date = fields.Date.to_date(order.date_order)
                    order_month = order_date.replace(day=1)
                    key = order_month.strftime('%b %y')
                    if key in month_totals:
                        month_totals[key] += order.amount_total
                        month_order_counts[key] += 1

                this_key = this_month_start.strftime('%b %y')
                prev_key = prev_month_start.strftime('%b %y')
                this_month_value = month_totals.get(this_key, 0.0)
                prev_month_value = month_totals.get(prev_key, 0.0)
                if prev_month_orders:
                    growth_orders_pct = ((this_month_orders - prev_month_orders) / prev_month_orders) * 100.0
                elif this_month_orders:
                    growth_orders_pct = 100.0
                if prev_month_value:
                    growth_value_pct = ((this_month_value - prev_month_value) / prev_month_value) * 100.0
                elif this_month_value:
                    growth_value_pct = 100.0

                if month_totals:
                    best_month_label, best_month_value = max(month_totals.items(), key=lambda x: x[1])

                if total_value:
                    old_vs_order_ratio = (old_sales_total / total_value) * 100.0

                # Product/Category/Company/Salesperson splits from sale orders
                product_value = defaultdict(float)
                category_value = defaultdict(float)
                company_value = defaultdict(float)
                salesperson_value = defaultdict(float)
                product_order_count = defaultdict(int)

                order_lines = orders.mapped('order_line').filtered(lambda l: not l.display_type and l.product_id)
                for line in order_lines:
                    p_name = line.product_id.display_name or "Unknown Product"
                    c_name = line.product_id.categ_id.display_name or "Uncategorized"
                    line_value = line.price_subtotal or 0.0
                    product_value[p_name] += line_value
                    category_value[c_name] += line_value
                    product_order_count[line.product_id.id] += 1

                for order in orders:
                    comp = order.company_id.name or "No Company"
                    usr = order.user_id.name or "No Salesperson"
                    company_value[comp] += order.amount_total or 0.0
                    salesperson_value[usr] += order.amount_total or 0.0

                def _build_rank_bars(data_map, top_n=5, money=True, currency_symbol=''):
                    if not data_map:
                        return "<div style='font-size:12px;color:#6b7280;'>No data</div>"
                    sorted_items = sorted(data_map.items(), key=lambda x: x[1], reverse=True)[:top_n]
                    max_val = sorted_items[0][1] or 1.0
                    rows = []
                    for idx, (label, val) in enumerate(sorted_items):
                        width = int((val / max_val) * 100) if max_val > 0 else 0
                        color = _color_palette()[idx % len(_color_palette())]
                        val_label = _fmt_money(val, currency_symbol) if money else f"{val:,.2f}"
                        rows.append(
                            "<div style='display:flex;align-items:center;gap:8px;margin:6px 0;'>"
                            f"<div style='width:150px;font-size:11px;color:#444;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{label}</div>"
                            "<div style='flex:1;background:#eef2f7;border-radius:4px;height:14px;overflow:hidden;'>"
                            f"<div style='height:14px;width:{width}%;background:{color};'></div></div>"
                            f"<div style='width:115px;text-align:right;font-size:11px;color:#333;'>{val_label}</div>"
                            "</div>"
                        )
                    return "".join(rows)

                currency_symbol = lead.company_id.currency_id.symbol or ''
                top_products_html = _build_rank_bars(product_value, top_n=10, money=True, currency_symbol=currency_symbol)
                top_categories_html = _build_rank_bars(category_value, top_n=6, money=True, currency_symbol=currency_symbol)
                company_split_html = _build_rank_bars(company_value, top_n=5, money=True, currency_symbol=currency_symbol)
                salesperson_split_html = _build_rank_bars(salesperson_value, top_n=5, money=True, currency_symbol=currency_symbol)

                repeat_products = sum(1 for cnt in product_order_count.values() if cnt > 1)
                one_time_products = sum(1 for cnt in product_order_count.values() if cnt == 1)
                mix_total = repeat_products + one_time_products
                repeat_pct = (repeat_products / mix_total * 100.0) if mix_total else 0.0
                one_time_pct = 100.0 - repeat_pct if mix_total else 0.0
                product_mix_html = (
                    "<div style='margin-top:8px;'>"
                    "<div style='display:flex;justify-content:space-between;font-size:11px;color:#444;margin-bottom:4px;'>"
                    f"<span>Repeat Items: {repeat_products}</span><span>{repeat_pct:.1f}%</span></div>"
                    "<div style='background:#eef2f7;border-radius:8px;overflow:hidden;height:16px;display:flex;'>"
                    f"<div style='width:{repeat_pct:.1f}%;background:#2563eb;'></div>"
                    f"<div style='width:{one_time_pct:.1f}%;background:#10b981;'></div>"
                    "</div>"
                    "<div style='display:flex;justify-content:space-between;font-size:11px;color:#444;margin-top:4px;'>"
                    f"<span>One-time Items: {one_time_products}</span><span>{one_time_pct:.1f}%</span></div>"
                    "</div>"
                )

                # Recency & frequency metrics
                if orders and orders[0].date_order:
                    days_since_last = (fields.Date.today() - fields.Date.to_date(orders[0].date_order)).days
                    if days_since_last <= 30:
                        recency_bucket = "Active (0-30 days)"
                    elif days_since_last <= 60:
                        recency_bucket = "Warm (31-60 days)"
                    else:
                        recency_bucket = "Dormant (60+ days)"

                order_dates = sorted(
                    [fields.Date.to_date(o.date_order) for o in orders if o.date_order]
                )
                if len(order_dates) >= 2:
                    gaps = [(order_dates[i] - order_dates[i - 1]).days for i in range(1, len(order_dates))]
                    avg_days_between_orders = sum(gaps) / len(gaps) if gaps else 0.0

            symbol = lead.company_id.currency_id.symbol or ''
            max_month_value = max(month_totals.values()) if month_totals else 0.0
            bars = []
            for label, value in month_totals.items():
                width = 0 if max_month_value <= 0 else int((value / max_month_value) * 100)
                bars.append(
                    "<div style='display:flex;align-items:center;gap:8px;margin:6px 0;'>"
                    f"<div style='width:55px;font-size:11px;color:#666;'>{label}</div>"
                    "<div style='flex:1;background:#eef2f7;border-radius:4px;height:18px;overflow:hidden;'>"
                    f"<div style='height:18px;width:{width}%;background:#2563eb;'></div></div>"
                    f"<div style='width:115px;text-align:right;font-size:11px;color:#333;'>{_fmt_money(value, symbol)}</div>"
                    "</div>"
                )

            max_order_count = max(month_order_counts.values()) if month_order_counts else 0
            order_bars = []
            for label, count in month_order_counts.items():
                width = 0 if max_order_count <= 0 else int((count / max_order_count) * 100)
                order_bars.append(
                    "<div style='display:flex;align-items:center;gap:8px;margin:5px 0;'>"
                    f"<div style='width:55px;font-size:11px;color:#666;'>{label}</div>"
                    "<div style='flex:1;background:#eef2f7;border-radius:4px;height:14px;overflow:hidden;'>"
                    f"<div style='height:14px;width:{width}%;background:#10b981;'></div></div>"
                    f"<div style='width:40px;text-align:right;font-size:11px;color:#333;'>{count}</div>"
                    "</div>"
                )

            growth_orders_color = "#16a34a" if growth_orders_pct >= 0 else "#dc2626"
            growth_value_color = "#16a34a" if growth_value_pct >= 0 else "#dc2626"

            lead.total_sales_orders_html = (
                "<div style='padding:14px;border:1px solid #d8dee8;border-radius:10px;background:#fbfcfe;"
                "font-family:Arial,sans-serif;line-height:1.35;word-break:normal;white-space:normal;width:100%;'>"
                "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:12px;'>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Total Sales Orders</div>"
                f"<div style='font-size:24px;font-weight:700;color:#111827;'>{total_orders}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Total Sales Value</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{_fmt_money(total_value, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Average Order Value</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{_fmt_money(avg_order_value, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Orders This Month</div>"
                f"<div style='font-size:22px;font-weight:700;color:#111827;'>{this_month_orders}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Old Sales Records</div>"
                f"<div style='font-size:22px;font-weight:700;color:#111827;'>{old_sales_count}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Old Sales Total</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{_fmt_money(old_sales_total, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>This Month Sales Value</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{_fmt_money(this_month_value, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Prev Month Sales Value</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{_fmt_money(prev_month_value, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Order Growth (MoM)</div>"
                f"<div style='font-size:20px;font-weight:700;color:{growth_orders_color};'>{_fmt_pct(growth_orders_pct)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Value Growth (MoM)</div>"
                f"<div style='font-size:20px;font-weight:700;color:{growth_value_color};'>{_fmt_pct(growth_value_pct)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Best Month</div>"
                f"<div style='font-size:18px;font-weight:700;color:#111827;'>{best_month_label}</div>"
                f"<div style='font-size:13px;color:#334155;'>{_fmt_money(best_month_value, symbol)}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Old Sales vs Orders Value</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{old_vs_order_ratio:.1f}%</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Recency Bucket</div>"
                f"<div style='font-size:16px;font-weight:700;color:#111827;'>{recency_bucket}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Avg Days Between Orders</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{avg_days_between_orders:.1f}</div></div>"
                "<div style='padding:10px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='font-size:11px;color:#6b7280;'>Lead to First Order</div>"
                f"<div style='font-size:20px;font-weight:700;color:#111827;'>{conversion_days} days</div>"
                f"<div style='font-size:11px;color:#6b7280;'>First order: {first_order_date}</div></div>"
                "</div>"
                "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:10px;'>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
                "<h4 style='margin:0;font-size:14px;color:#111827;'>Sales Trend (Last 12 Months)</h4>"
                f"<span style='font-size:12px;color:#6b7280;'>Last Order: {last_order_date}</span>"
                "</div>"
                f"{''.join(bars)}"
                "</div>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Order Count Trend (Last 12 Months)</h4>"
                f"{''.join(order_bars)}"
                "</div>"
                "</div>"
                "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:10px;margin-top:10px;'>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Top 10 Purchased Items (Value)</h4>"
                f"{top_products_html}"
                "</div>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Top Categories Ordered</h4>"
                f"{top_categories_html}"
                "</div>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Company-wise Sales Split</h4>"
                f"{company_split_html}"
                "</div>"
                "<div style='padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Salesperson-wise Sales Split</h4>"
                f"{salesperson_split_html}"
                "</div>"
                "</div>"
                "<div style='margin-top:10px;padding:12px;border:1px solid #e6ebf3;border-radius:8px;background:white;'>"
                "<h4 style='margin:0 0 8px 0;font-size:14px;color:#111827;'>Product Mix (Repeat vs One-time)</h4>"
                f"{product_mix_html}"
                "</div>"
                "</div>"
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

