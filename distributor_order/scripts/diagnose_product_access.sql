-- Diagnose "Access Error / product.product read" for a distributor user.
-- Usage: edit \set uid below, then:
--   psql -U odoo -d YOUR_DATABASE -f diagnose_product_access.sql
-- Use the numeric id from the error (e.g. "id=120" -> res.users id 120).

\set uid 120

\echo '========== res.users =========='
SELECT u.id, u.login, u.active, u.share, u.company_id AS default_company_id, p.name AS partner_name
FROM res_users u
JOIN res_partner p ON p.id = u.partner_id
WHERE u.id = :uid;

\echo '========== User companies (res_company_users_rel) =========='
SELECT c.id, c.name
FROM res_company c
JOIN res_company_users_rel r ON r.cid = c.id
WHERE r.user_id = :uid;

\echo '========== Groups for this user =========='
SELECT g.id, g.name::text AS name_json
FROM res_groups g
JOIN res_groups_users_rel rel ON rel.gid = g.id
WHERE rel.uid = :uid
ORDER BY g.id;

\echo '========== ir.model.access for product.product intersecting user groups =========='
SELECT a.id, a.name, a.group_id, a.perm_read, a.perm_write, a.perm_create, a.perm_unlink, g.name::text AS group_name
FROM ir_model_access a
JOIN ir_model m ON m.id = a.model_id
LEFT JOIN res_groups g ON g.id = a.group_id
WHERE m.model = 'product.product'
  AND (a.group_id IN (SELECT gid FROM res_groups_users_rel WHERE uid = :uid) OR a.group_id IS NULL)
ORDER BY a.group_id NULLS LAST, a.id;

\echo '========== ir.rule for product.product and product.template =========='
SELECT r.id, r.name, r.active, r.global, m.model, r.perm_read, r.perm_write,
       r.domain_force,
       (SELECT string_agg(gr.group_id::text, ', ' ORDER BY gr.group_id)
        FROM rule_group_rel gr WHERE gr.rule_group_id = r.id) AS group_ids
FROM ir_rule r
JOIN ir_model m ON m.id = r.model_id
WHERE m.model IN ('product.product', 'product.template')
ORDER BY m.model, r.id;

\echo '========== distributor_order module =========='
SELECT name, state, latest_version
FROM ir_module_module
WHERE name = 'distributor_order';
