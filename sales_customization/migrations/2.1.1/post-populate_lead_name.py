def migrate(cr, version):
    cr.execute("""
        UPDATE crm_lead_old_sale AS os
           SET lead_name = cl.name
          FROM crm_lead AS cl
         WHERE os.lead_id = cl.id
           AND (os.lead_name IS NULL OR os.lead_name = '')
    """)
