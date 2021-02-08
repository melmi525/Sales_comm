# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'Sales Commission (Enterprise)',
    'summary': 'Commission to Sales Person',
    'version': '1.0',
    'description' :"""Sales Commission.""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Sales',
    'website': "http://www.acespritech.com",
    'price': 40,
    'currency': 'EUR',
    'depends' : ['base', 'stock', 'sale', 'sale_management', 'account', 'hr_payroll', 'sale_margin',
                 'hr_payroll_account'],
    'data' : [
        'security/ir.model.access.csv',
        'views/sale_invoice_scheduler.xml',
        'views/sale_team_view.xml',
        'views/sale_view.xml',
        'views/product_view.xml',
        'views/sales_commission.xml',
        'views/hr_payroll_view.xml',
        'views/hr_payroll_data.xml',
        'views/account_view.xml',
        'views/res_company_views.xml',
        'report/print_commission_summary_template.xml',
        'report/report.xml',
        'wizard/sales_commission_payment_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 
