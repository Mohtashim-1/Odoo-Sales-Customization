#!/usr/bin/env python3
"""
Script to check product income account configuration in Odoo database
"""
import sys
import os

# Add Odoo to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo import api, SUPERUSER_ID

# Database connection - adjust these if needed
db_name = 'odoo'  # Change if your database name is different
odoo.tools.config.parse_config(['-d', db_name])

# Initialize Odoo
odoo.service.db.ensure_db()
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find the product
    product = env['product.template'].search([
        ('name', 'ilike', 'Vital Cardamom Tea Premix')
    ], limit=1)
    
    if not product:
        print("ERROR: Product 'Vital Cardamom Tea Premix' not found!")
        sys.exit(1)
    
    print(f"\n=== Product Found ===")
    print(f"Product ID: {product.id}")
    print(f"Product Name: {product.name}")
    
    # Get company
    company = env['res.company'].search([
        ('name', 'ilike', 'Eastern Products')
    ], limit=1)
    
    if company:
        print(f"\n=== Company Found ===")
        print(f"Company ID: {company.id}")
        print(f"Company Name: {company.name}")
        
        # Check property_account_income_id with company context
        product_company = product.with_company(company)
        account = product_company.property_account_income_id
        
        print(f"\n=== Income Account (with company context) ===")
        if account:
            print(f"Account ID: {account.id}")
            print(f"Account Code: {account.code}")
            print(f"Account Name: {account.name}")
            print(f"Account Company: {account.company_id.name}")
            print(f"Account Deprecated: {account.deprecated}")
        else:
            print("NO ACCOUNT FOUND!")
        
        # Check using _get_product_accounts
        print(f"\n=== Using _get_product_accounts method ===")
        try:
            accounts = product._get_product_accounts()
            print(f"Accounts dict: {accounts}")
            income_account = accounts.get('income')
            if income_account:
                print(f"Income Account ID: {income_account.id}")
                print(f"Income Account Code: {income_account.code}")
                print(f"Income Account Name: {income_account.name}")
            else:
                print("NO INCOME ACCOUNT IN _get_product_accounts!")
        except Exception as e:
            print(f"Error calling _get_product_accounts: {e}")
        
        # Check ir.property directly
        print(f"\n=== Checking ir.property table ===")
        prop = env['ir.property'].search([
            ('res_id', '=', f'product.template,{product.id}'),
            ('name', '=', 'property_account_income_id'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if prop:
            print(f"Property found: {prop.id}")
            print(f"Value reference: {prop.value_reference}")
            if prop.value_reference:
                model, account_id = prop.value_reference.split(',')
                account_obj = env[model].browse(int(account_id))
                print(f"Account from property: {account_obj.name} ({account_obj.code})")
        else:
            print("NO PROPERTY FOUND in ir.property!")
            
            # Check without company
            prop_no_company = env['ir.property'].search([
                ('res_id', '=', f'product.template,{product.id}'),
                ('name', '=', 'property_account_income_id'),
                ('company_id', '=', False)
            ], limit=1)
            if prop_no_company:
                print(f"Found property without company: {prop_no_company.value_reference}")
        
        # Check category
        if product.categ_id:
            print(f"\n=== Product Category ===")
            print(f"Category: {product.categ_id.name}")
            cat_account = product.categ_id.property_account_income_categ_id
            if cat_account:
                print(f"Category Income Account: {cat_account.name} ({cat_account.code})")
            else:
                print("NO CATEGORY INCOME ACCOUNT!")
        
        # Search for Sales Income account
        print(f"\n=== Searching for 'Sales Income' account ===")
        sales_income_account = env['account.account'].search([
            ('name', 'ilike', 'Sales Income'),
            ('company_id', '=', company.id)
        ], limit=1)
        if sales_income_account:
            print(f"Found: {sales_income_account.name} ({sales_income_account.code})")
        else:
            print("NOT FOUND!")
            
        # Search for account 3111001
        print(f"\n=== Searching for account code 3111001 ===")
        account_3111001 = env['account.account'].search([
            ('code', '=', '3111001'),
            ('company_id', '=', company.id)
        ], limit=1)
        if account_3111001:
            print(f"Found: {account_3111001.name} ({account_3111001.code})")
        else:
            print("NOT FOUND!")

