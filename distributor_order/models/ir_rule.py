import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def action_distributor_cleanup_legacy_product_rules(self, **kwargs):
        """Remove ir.rules on ``product.product`` that break reads for Sale/Customer users.

        Called from ``data/cleanup_product_access_rules.xml`` on every upgrade (noupdate=0).

        A legacy rule used ``brand_id`` on variants (field lives on ``product.template``). Users
        who are both **Sale/Customer Group** and **Distributor User** then could not read variants.
        We remove:
        - the known XML id ``sale_brand_filter.product_brand_filter_rule`` if present;
        - any rule on ``product.product`` whose domain still references ``brand_id`` without
          ``product_tmpl_id``;
        - any rule on ``product.product`` that applies to **Sale/Customer Group** (that group
          implies Internal User and should not carry extra variant-level brand rules here).
        """
        Rule = self.sudo()
        Product = self.env['ir.model'].sudo().search([('model', '=', 'product.product')], limit=1)
        if not Product:
            return True

        xml_rule = self.env.ref('sale_brand_filter.product_brand_filter_rule', raise_if_not_found=False)
        if xml_rule:
            _logger.info('distributor_order: unlink ir.rule %s', xml_rule.display_name)
            xml_rule.unlink()

        bad_domain = Rule.search([
            ('model_id', '=', Product.id),
            ('domain_force', 'ilike', 'brand_id'),
            ('domain_force', 'not ilike', 'product_tmpl_id'),
        ])
        if bad_domain:
            _logger.warning(
                'distributor_order: unlink %s product.product rule(s) (brand_id on variant domain)',
                len(bad_domain),
            )
            bad_domain.unlink()

        # Global rules (no groups) with the same broken domain affect everyone.
        global_bad = Rule.search([
            ('model_id', '=', Product.id),
            ('groups', '=', False),
            ('domain_force', 'ilike', 'brand_id'),
            ('domain_force', 'not ilike', 'product_tmpl_id'),
        ])
        if global_bad:
            _logger.warning(
                'distributor_order: unlink %s global product.product rule(s) (brand_id on variant)',
                len(global_bad),
            )
            global_bad.unlink()

        cust = self.env.ref('sales_customization.sales_customer_group', raise_if_not_found=False)
        if cust:
            customer_product_rules = Rule.search([('model_id', '=', Product.id)]).filtered(
                lambda r: cust in r.groups
                and (
                    len(r.groups) == 1
                    or (
                        r.domain_force
                        and 'brand_id' in r.domain_force.lower()
                        and 'product_tmpl_id' not in r.domain_force.lower()
                    )
                )
            )
            if customer_product_rules:
                _logger.warning(
                    'distributor_order: unlink %s product.product rule(s) for Sale/Customer Group '
                    '(single-group or broken brand_id on variant)',
                    len(customer_product_rules),
                )
                customer_product_rules.unlink()

        return True
