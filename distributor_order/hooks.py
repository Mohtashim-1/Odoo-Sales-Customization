import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(*args):
    """Delegate to ``ir.rule.action_distributor_cleanup_legacy_product_rules``."""
    if len(args) == 1:
        env = args[0]
    else:
        cr, _registry = args[0], args[1]
        env = api.Environment(cr, SUPERUSER_ID, {})

    env['ir.rule'].sudo().action_distributor_cleanup_legacy_product_rules()
