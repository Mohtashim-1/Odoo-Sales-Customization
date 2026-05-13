from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class DistributorOrder(models.Model):
    _name = 'distributor.order'
    _description = 'Distributor Order'
    _order = 'order_date desc, name desc'
    _inherit = ['product.catalog.mixin', 'mail.thread', 'mail.activity.mixin']

    # ─── Identity ──────────────────────────────────────────────────────────────

    name = fields.Char(
        string='Order Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('sale_created', 'Sale Order Created'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # ─── Parties ───────────────────────────────────────────────────────────────

    distributor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Distributor',
        required=True,
        default=lambda self: self._default_distributor_id(),
        domain=[('is_distributor', '=', True)],
        tracking=True,
        index=True,
    )
    can_edit_distributor_id = fields.Boolean(
        compute='_compute_can_edit_distributor_id',
    )
    can_edit_salesperson_id = fields.Boolean(
        compute='_compute_can_edit_distributor_id',
    )
    salesperson_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        domain=[('share', '=', False)],
        tracking=True,
        index=True,
    )

    # ─── Dates ─────────────────────────────────────────────────────────────────

    order_date = fields.Date(
        string='Order Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    submission_date = fields.Datetime(
        string='Submitted On',
        readonly=True,
        copy=False,
    )
    approval_date = fields.Datetime(
        string='Approved / Rejected On',
        readonly=True,
        copy=False,
    )

    # ─── Lines & Totals ────────────────────────────────────────────────────────

    order_line_ids = fields.One2many(
        comodel_name='distributor.order.line',
        inverse_name='order_id',
        string='Order Lines',
        copy=True,
    )
    amount_total = fields.Float(
        string='Total Amount',
        compute='_compute_amount_total',
        store=True,
        digits='Account',
    )
    total_ctn = fields.Float(
        string='Total Ctn',
        compute='_compute_totals_ctn_cbm',
        store=True,
        digits='Product Unit of Measure',
        help='Sum of order line quantities (same UoM as each line).',
    )
    total_cbm = fields.Float(
        string='Total CBM',
        compute='_compute_totals_ctn_cbm',
        store=True,
        digits=(16, 4),
        help='Sum of line quantity × product CBM (from product template).',
    )

    # ─── Notes & Rejection ─────────────────────────────────────────────────────

    notes = fields.Html(string='Terms and Conditions')
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
        tracking=True,
    )

    # ─── Currency (from company) ───────────────────────────────────────────────

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )

    # ─── Linked Sale Order ─────────────────────────────────────────────────────

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # ─── Computes ──────────────────────────────────────────────────────────────

    @api.depends('order_line_ids.price_subtotal')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.order_line_ids.mapped('price_subtotal'))

    @api.depends(
        'order_line_ids.product_qty',
        'order_line_ids.product_id',
        'order_line_ids.product_id.product_tmpl_id.cbm',
    )
    def _compute_totals_ctn_cbm(self):
        for order in self:
            total_ctn = 0.0
            total_cbm = 0.0
            for line in order.order_line_ids:
                qty = line.product_qty or 0.0
                total_ctn += qty
                tmpl = line.product_id.product_tmpl_id
                total_cbm += qty * (tmpl.cbm or 0.0)
            order.total_ctn = total_ctn
            order.total_cbm = total_cbm

    def _compute_can_edit_distributor_id(self):
        can_edit = (
            self.env.user.has_group('distributor_order.group_distributor_salesperson')
            or self.env.user.has_group('distributor_order.group_distributor_manager')
        )
        for order in self:
            order.can_edit_distributor_id = can_edit
            order.can_edit_salesperson_id = can_edit

    # ─── Onchanges ─────────────────────────────────────────────────────────────

    @api.onchange('distributor_id')
    def _onchange_distributor_id(self):
        if self.distributor_id:
            self.salesperson_id = self._get_distributor_salesperson(self.distributor_id)

    @api.model
    def _get_distributor_salesperson(self, distributor):
        if not distributor:
            return self.env['res.users']
        # Assigned salesperson on the partner (do not use partner.user_ids — distributor logins are internal too).
        if distributor.distributor_salesperson_id:
            return distributor.distributor_salesperson_id
        return self.env['res.users']

    @api.model
    def _get_current_user_distributor(self):
        user = self.env.user
        commercial_partner = user.partner_id.commercial_partner_id
        distributor_partners = self.env['res.partner'].search([
            ('is_distributor', '=', True),
            ('user_ids', 'in', user.id),
        ])

        if commercial_partner.is_distributor and commercial_partner in distributor_partners:
            return commercial_partner
        if len(distributor_partners) == 1:
            return distributor_partners
        if not distributor_partners and commercial_partner.is_distributor:
            return commercial_partner
        if len(distributor_partners) > 1:
            raise UserError(_(
                'Your user is linked to multiple distributor records. '
                'Please contact your administrator.'
            ))
        return self.env['res.partner']

    @api.model
    def _default_distributor_id(self):
        distributor = self._get_current_user_distributor()
        return distributor.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'distributor_id' in fields_list and not res.get('distributor_id'):
            distributor = self._get_current_user_distributor()
            if distributor:
                res['distributor_id'] = distributor.id
                salesperson = self._get_distributor_salesperson(distributor)
                res.setdefault('salesperson_id', salesperson.id)
        return res

    # ─── ORM overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        current_user_distributor = self._get_current_user_distributor()
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('distributor.order') or 'New'
            if (
                self.env.user.has_group('distributor_order.group_distributor_user')
                and not self.env.user.has_group('distributor_order.group_distributor_salesperson')
            ):
                if not current_user_distributor:
                    raise UserError(_(
                        'No distributor is linked to your user. Please contact your administrator.'
                    ))
                vals['distributor_id'] = current_user_distributor.id
                vals['salesperson_id'] = self._get_distributor_salesperson(current_user_distributor).id
        return super().create(vals_list)

    def write(self, vals):
        if (
            ('distributor_id' in vals or 'salesperson_id' in vals)
            and self.env.user.has_group('distributor_order.group_distributor_user')
            and not self.env.user.has_group('distributor_order.group_distributor_salesperson')
        ):
            current_user_distributor = self._get_current_user_distributor()
            if not current_user_distributor:
                raise UserError(_(
                    'No distributor is linked to your user. Please contact your administrator.'
                ))
            vals['distributor_id'] = current_user_distributor.id
            vals['salesperson_id'] = self._get_distributor_salesperson(current_user_distributor).id
        return super().write(vals)

    def _default_order_line_values(self):
        default_data = super()._default_order_line_values()
        new_default_data = self.env['distributor.order.line']._get_product_catalog_lines_data()
        return {**default_data, **new_default_data}

    def _get_action_add_from_catalog_extra_context(self):
        return {
            **super()._get_action_add_from_catalog_extra_context(),
            'product_catalog_currency_id': self.currency_id.id,
            'product_catalog_digits': self.order_line_ids._fields['price_unit'].get_digits(self.env),
        }

    def _get_product_catalog_domain(self):
        domain = [('sale_ok', '=', True)]
        user = self.env.user
        if (
            user.has_group('distributor_order.group_distributor_user')
            and not user.has_group('distributor_order.group_distributor_salesperson')
            and user.distributor_allowed_brand_ids
        ):
            domain = expression.AND([
                domain,
                [('product_tmpl_id.brand_id', 'in', user.distributor_allowed_brand_ids.ids)],
            ])
        return domain

    def _get_product_catalog_order_data(self, products, **kwargs):
        res = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            res[product.id]['price'] = product.lst_price
        return res

    def _get_product_catalog_record_lines(self, product_ids, **kwargs):
        grouped_lines = defaultdict(lambda: self.env['distributor.order.line'])
        for line in self.order_line_ids:
            if line.product_id.id not in product_ids:
                continue
            grouped_lines[line.product_id] |= line
        return grouped_lines

    def _get_parent_field_on_child_model(self):
        return 'order_id'

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        self.ensure_one()
        line = self.order_line_ids.filtered(lambda l: l.product_id.id == product_id)[:1]
        product = self.env['product.product'].browse(product_id)
        if line:
            if quantity > 0:
                line.product_qty = quantity
            elif self.state == 'draft':
                price_unit = product.lst_price
                line.unlink()
                return price_unit
            else:
                line.product_qty = 0
            return line.price_unit
        if quantity > 0:
            line = self.env['distributor.order.line'].create({
                'order_id': self.id,
                'product_id': product_id,
                'product_qty': quantity,
                'price_unit': product.lst_price,
                'description': product.description_sale or '',
            })
            return line.price_unit
        return product.lst_price

    def _is_readonly(self):
        self.ensure_one()
        return self.state != 'draft'

    # ─── Workflow Actions ──────────────────────────────────────────────────────

    def action_submit(self):
        """Distributor submits the order to their salesperson for review."""
        for order in self:
            if order.state != 'draft':
                raise UserError(_('Only draft orders can be submitted.'))
            if not order.order_line_ids:
                raise UserError(_('Please add at least one product before submitting.'))
            if not order.salesperson_id:
                raise UserError(
                    _('No salesperson is assigned to this distributor. '
                      'Please contact your administrator.')
                )
            order.write({
                'state': 'submitted',
                'submission_date': fields.Datetime.now(),
            })
            order.message_post(
                body=_('Order submitted for approval to %s.', order.salesperson_id.name),
                subtype_xmlid='mail.mt_note',
            )
            # Notify the salesperson
            order.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=order.salesperson_id.id,
                note=_('Distributor order %s from %s is waiting for your approval.',
                        order.name, order.distributor_id.name),
            )

    def action_approve(self):
        """Salesperson approves the order and creates a Sale Order."""
        for order in self:
            if order.state != 'submitted':
                raise UserError(_('Only submitted orders can be approved.'))
            sale_order = order._create_sale_order()
            order.write({
                'state': 'approved',
                'approval_date': fields.Datetime.now(),
                'sale_order_id': sale_order.id,
            })
            order.message_post(
                body=_('Order approved. Sale Order <a href="#" data-oe-model="sale.order" '
                        'data-oe-id="%d">%s</a> has been created.', sale_order.id, sale_order.name),
                subtype_xmlid='mail.mt_note',
            )
            # Mark pending activities done
            order.activity_ids.filtered(
                lambda a: a.activity_type_id.id == self.env.ref('mail.mail_activity_data_todo').id
            ).action_done()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
        }

    def action_reject(self):
        """Open a wizard / inline dialog to collect rejection reason then reject."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Order'),
            'res_model': 'distributor.order.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def action_reset_draft(self):
        """Reset a rejected order back to draft."""
        for order in self:
            if order.state not in ('rejected', 'draft'):
                raise UserError(_('Only rejected orders can be reset to draft.'))
            order.write({
                'state': 'draft',
                'rejection_reason': False,
            })

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
        }

    # ─── Internal helpers ──────────────────────────────────────────────────────

    def _create_sale_order(self):
        """Create and confirm a sale.order from this distributor order."""
        self.ensure_one()
        SaleOrder = self.env['sale.order']
        so_vals = {
            'partner_id': self.distributor_id.id,
            'user_id': self.salesperson_id.id,
            'company_id': self.company_id.id,
            'client_order_ref': self.name,
            'note': self.notes or '',
            'order_line': [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'name': line.description or line.product_id.display_name,
                })
                for line in self.order_line_ids
            ],
        }
        sale_order = SaleOrder.create(so_vals)
        return sale_order


# ─── Rejection Wizard ──────────────────────────────────────────────────────────

class DistributorOrderRejectWizard(models.TransientModel):
    _name = 'distributor.order.reject.wizard'
    _description = 'Distributor Order Rejection Wizard'

    order_id = fields.Many2one(
        comodel_name='distributor.order',
        string='Order',
        required=True,
        readonly=True,
    )
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_rejection(self):
        self.ensure_one()
        order = self.order_id
        if order.state != 'submitted':
            raise UserError(_('Only submitted orders can be rejected.'))
        order.write({
            'state': 'rejected',
            'approval_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason,
        })
        order.message_post(
            body=_('Order rejected. Reason: %s', self.rejection_reason),
            subtype_xmlid='mail.mt_note',
        )
        order.activity_ids.filtered(
            lambda a: a.activity_type_id.id == self.env.ref('mail.mail_activity_data_todo').id
        ).action_feedback(feedback=_('Rejected: %s', self.rejection_reason))
        return {'type': 'ir.actions.act_window_close'}
