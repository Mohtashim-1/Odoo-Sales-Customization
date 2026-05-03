from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _filter_access_rules_python(self, operation):
        # Record rules on product.product (e.g. legacy brand domains) can still raise
        # AccessError on read() even when ACLs allow read and SQL search returns ids.
        # Distributor users need stable read access for order lines and related prefetch.
        if (
            operation == 'read'
            and not self.env.su
            and self.env.user.has_group('distributor_order.group_distributor_user')
        ):
            return self
        return super()._filter_access_rules_python(operation)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = list(domain or [])
        if self.env.context.get('from_distributor_order_line'):
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
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid,
        )
