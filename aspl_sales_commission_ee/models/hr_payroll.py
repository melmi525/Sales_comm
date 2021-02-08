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

from odoo import models, fields, api, _


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    sale_commission_amount = fields.Float(string="Commission Amount", readonly=True, copy=False)

    def compute_sheet(self):
        comm_obj = self.env['sales.commission']
        for payslip in self:
            commission = 0.0
            if payslip.employee_id.user_id:
                comm_ids = comm_obj.search([('user_id', '=', payslip.employee_id.user_id.id),
                                            ('commission_date', '>=', payslip.date_from),
                                            ('commission_date', '<=', payslip.date_to),
                                            ('pay_by', '=', 'salary'), ('state', '=', 'draft')])
                commission = sum([commid.amount for commid in comm_ids])
            payslip.sale_commission_amount = commission
        return super(hr_payslip, self).compute_sheet()

    def action_payslip_done(self):
        res = super(hr_payslip, self).action_payslip_done()
        comm_obj = self.env['sales.commission']
        comm_rule_id = self.env.ref('aspl_sales_commission_ee.hr_salary_rule_aspl_sales_commission')
        if comm_rule_id:
            for payslip in self:
                if payslip.employee_id.user_id and comm_rule_id.id in [line.salary_rule_id.id for line in payslip.line_ids]:
                    comm_ids = comm_obj.search([('user_id', '=', payslip.employee_id.user_id.id),
                                                ('commission_date', '>=', payslip.date_from),
                                                ('commission_date', '<=', payslip.date_to),
                                                ('pay_by', '=', 'salary'), ('state', '=', 'draft')])
                    comm_ids.write({'state': 'paid', 'payslip_id': payslip.id})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: