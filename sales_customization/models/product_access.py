from odoo import _
from odoo.exceptions import AccessError

# Groups allowed to create products (item master). Everyone else is blocked,
# including quick-create from sale order lines.
PRODUCT_CREATE_GROUP_XIDS = (
    'sales_team.group_sale_manager',
    'stock.group_stock_manager',
    'purchase.group_purchase_manager',
    'mrp.group_mrp_manager',
    'point_of_sale.group_pos_manager',
    'base.group_system',
)


def check_product_create_access(env):
    if env.su:
        return
    if any(env.user.has_group(xid) for xid in PRODUCT_CREATE_GROUP_XIDS):
        return
    raise AccessError(
        _('You are not allowed to create products. Please ask a product administrator.')
    )
