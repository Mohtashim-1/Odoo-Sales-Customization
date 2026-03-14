from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    group_user = env.ref("base.group_user", raise_if_not_found=False)
    if not group_user:
        return

    for xml_id in (
        "sales_customization.sales_customer_group",
        "sales_customization.sales_document_group",
    ):
        group = env.ref(xml_id, raise_if_not_found=False)
        if not group:
            continue
        users = env["res.users"].with_context(active_test=False).search(
            [("groups_id", "in", group.id), ("groups_id", "not in", group_user.id)]
        )
        if users:
            users.write({"groups_id": [(4, group_user.id)]})

    # Force update of Sale's personal rule domain (noupdate in core)
    rule = env.ref("sale.sale_order_personal_rule", raise_if_not_found=False)
    if rule:
        rule.write({"domain_force": "[('user_id', '=', user.id)]"})
