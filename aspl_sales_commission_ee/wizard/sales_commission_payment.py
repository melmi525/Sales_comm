# coding=utf-8
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
from odoo.exceptions import Warning
from datetime import datetime


class SalesCommissionPayment(models.TransientModel):
    _name = 'sales.commission.payment'

    def generate_invoice(self):
        invoice_obj = self.env['account.move']
        invoice_id = False
        domain = [('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                  '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel')]
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning(_('End Date should be greater than Start Date.'))
            domain.append(('commission_date', '>=', self.start_date))
            domain.append(('commission_date', '<=', self.end_date))
        if self.user_id:
            domain += [('user_id', '=', self.user_id.id),('partner_id', '=', False)]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        commission_ids = self._context.get('commission_ids')

        if not commission_ids:
            commission_ids = self.env['sales.commission'].search(domain)

        if commission_ids:
            journal_id = invoice_obj.with_context({
                                                    'default_type': 'in_invoice',
                                                   'default_company_id': self.env.user.company_id.id})._get_default_journal()
            if not journal_id:
                raise Warning(_('Account Journal not found.'))
            account_id = self.env.user.company_id and self.env.user.company_id.account_id
            if not account_id:
                raise Warning(
                    _('Commission Account is not Found. Please go to related Company and set the Commission account.'))
            else:
                inv_line_data = []
                if self.payment_for == 'customer':
                    partner_id = self.partner_id
                else:
                    partner_id = self.user_id.partner_id
                invoice_id = invoice_obj.search(
                    [('partner_id', '=', self.user_id.partner_id.id), ('state', '=', 'draft'),
                     ('type', '=', 'in_invoice'), ('commission_invoice', '=', True),
                     ('company_id', '=', self.env.user.company_id.id)])
                if invoice_id:
                    for commid in commission_ids:
                        inv_line_data.append((0, 0, {'account_id': account_id.id,
                                                     'name': commid.name + " Commission",
                                                     'quantity': 1,
                                                     'price_unit': commid.amount,
                                                     'sale_commission_id': commid.id,
                                                     # 'display_type':'line_section',
                                                     }))
                    invoice_id.write({'invoice_line_ids': inv_line_data, 'commission_invoice': True})
                else:
                    for commid in commission_ids:
                        inv_line_data.append((0, 0, {'account_id': account_id.id,
                                                     'name': commid.name + " Commission",
                                                     'quantity': 1,
                                                     'price_unit': commid.amount,
                                                     'sale_commission_id': commid.id,
                                                     }))

                    invoice_vals = {'partner_id': partner_id.id,
                                    'company_id': self.env.user.company_id.id,
                                    'commission_invoice': True,
                                    'type': 'in_invoice',
                                    'journal_id': journal_id.id,
                                    'invoice_line_ids': inv_line_data,
                                    'invoice_date_due': datetime.today(),
                                    }
                    invoice_id = invoice_obj.create(invoice_vals)
                    invoice_id._onchange_partner_id()
                for commid in commission_ids:
                    commid.write({'invoice_id': invoice_id.id, 'state': 'invoiced'})
            #
            if invoice_id:
                view_id = self.env.ref("account.view_move_form")
                return {
                    'name': "Commission Invoice",
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'view_id': view_id.id,
                    'view_mode': 'form',
                    'res_id': invoice_id.id,
                }
        else:
            raise Warning("No Commission line  Generated")


    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    payment_for = fields.Selection([('customer', 'Non Users'), ('user', 'User')], string="Payment For")
    user_id = fields.Many2one('res.users', string="User")
    partner_id = fields.Many2one('res.partner', string="Sales rep")


class wizard_commission_summary(models.TransientModel):
    _name = 'wizard.commission.summary'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    job_ids = fields.Many2many('hr.job', string="Job")
    payment_for = fields.Selection([('customer', 'Non Users'), ('user', 'User')], string="Payment For")
    user_ids = fields.Many2many('res.users', string="User(s)")
    partner_ids = fields.Many2many('res.partner', string="Sales rep")

    @api.onchange('job_ids')
    def onchange_job(self):
        res = {'value': {'user_ids': False}}
        if self.job_ids:
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', 'in', self.job_ids.ids)])
            user_lst = list(set([emp.user_id.id for emp in emp_ids]))
            res.update({'domain': {'user_ids': [('id', 'in', user_lst)]}})
            if self.env.context.get('ctx_job_user_report_print'):
                return user_lst
        return res

    def get_users_commission(self):
        result = {}
        user_ids = [user.id for user in self.user_ids or self.env['res.users'].search([])]
        # partner_ids = [parnter.id for parnter in self.partner_ids or self.env['res.partner'].search([])]
        partner_ids = [partner.id for partner in self.partner_ids or self.env['res.partner'].search([])]
        if not self.user_ids and self.job_ids:
            user_ids = self.with_context({'ctx_job_user_report_print': True}).onchange_job()
        domain = []
        if user_ids and self.payment_for == 'user':
            domain += [('user_id', 'in', user_ids), ('partner_id', '=', False)]
        if partner_ids and self.payment_for == 'customer':
            domain += [('partner_id', 'in', partner_ids)]
        if self.start_date and self.end_date:
            domain.append(('commission_date', '>=', str(self.start_date)))
            domain.append(('commission_date', '<=', str(self.end_date)))
        for commid in self.env['sales.commission'].search(domain, order="commission_date"):
            vals = {'name': commid.name,
                    'date': commid.commission_date,
                    'user_name': commid.user_id.name,
                    'partner_name': commid.partner_id.name,
                    'amount': commid.amount,
                    'payment_for': self.payment_for,
                    'pay_by': 'Invoice' if commid.pay_by == 'invoice' else 'Salary'}
            if self.payment_for == 'customer':
                if commid.partner_id.id in result:
                    result[commid.partner_id.id].append(vals)
                else:
                    result.update({commid.partner_id.id: [vals]})
            else:

                if commid.user_id.id in result:
                    result[commid.user_id.id].append(vals)
                else:
                    result.update({commid.user_id.id: [vals]})
        if not result:
            raise Warning(_('Sales Commission Details not found.'))
        return result

    def print_commission_report(self):
        if self.start_date > self.end_date:
            raise Warning(_('End Date should be greater than Start Date.'))
        datas = {
            'ids': self._ids,
            'model': 'wizard.commission.summary',
            'form': self.read()[0],
            'commission_details': self.get_users_commission()
        }
        return self.env.ref('aspl_sales_commission_ee.report_print_commission_summary').report_action(self, data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: