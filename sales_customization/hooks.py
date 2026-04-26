from odoo import SUPERUSER_ID, api


def post_init_hook(*args):
    # Odoo 18+: post_init_hook(env). Older versions: post_init_hook(cr, registry).
    if len(args) == 1:
        env = args[0]
    else:
        cr, _registry = args[0], args[1]
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

    # Force update of Sale rules whose XML is noupdate=1 in core (XML overrides may not apply).
    domain_mc = (
        "['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]"
    )
    for xmlid in (
        "sale.sale_order_comp_rule",
        "sale.sale_order_line_comp_rule",
        "sale.sale_order_report_comp_rule",
    ):
        mc_rule = env.ref(xmlid, raise_if_not_found=False)
        if mc_rule:
            mc_rule.write({"domain_force": domain_mc})

    rule = env.ref("sale.sale_order_personal_rule", raise_if_not_found=False)
    if rule:
        rule.write({"domain_force": "[('user_id', '=', user.id)]"})
