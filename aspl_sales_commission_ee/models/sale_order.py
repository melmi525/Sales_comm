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
from datetime import datetime
from lxml import etree
# from odoo.osv.orm import setup_modifiers
# from odoo.osv.orm import setup_modifiers


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(res_config_settings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        res.update({'commission_pay_on': param_obj.sudo().get_param('aspl_sales_commission_ee.commission_pay_on'),
                    'commission_calc': param_obj.sudo().get_param('aspl_sales_commission_ee.commission_calc'),
                    'commission_pay_by': param_obj.sudo().get_param('aspl_sales_commission_ee.commission_pay_by'),
                })
        return res

    def set_values(self):
        res = super(res_config_settings, self).set_values()
        param_obj = self.env['ir.config_parameter']
        param_obj.sudo().set_param('aspl_sales_commission_ee.commission_pay_on', self.commission_pay_on)
        param_obj.sudo().set_param('aspl_sales_commission_ee.commission_calc', self.commission_calc)
        param_obj.sudo().set_param('aspl_sales_commission_ee.commission_pay_by', self.commission_pay_by)

    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Commission Pay On")
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation")
    commission_pay_by = fields.Selection([('invoice', 'Invoice'), ('salary', 'Salary')], string="Commission Pay By")


class sales_order_commission(models.Model):
    _name = 'sales.order.commission'

    user_id = fields.Many2one('res.users', string="User")
    partner_id = fields.Many2one('res.partner', string="Sales Rep")
    job_id = fields.Many2one('hr.job', string="Job Position")
    commission = fields.Float(string="Commission")
    order_id = fields.Many2one('sale.order', string="Order")
    invoice_id = fields.Many2one('account.move', string="Invoice")


class sale_order(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        self.ensure_one()
        res = super(sale_order, self)._prepare_invoice()
        if res:
            res.update({'commission_calc': self.commission_calc, 'commission_pay_on': self.commission_pay_on})
        return res

    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        comm_obj = self.env['sales.commission']
        for saleid in self:
            comm_obj.search([('state', '=', 'draft'), ('sale_order_id', '=', saleid.id)]).write({'state': 'cancel'})
        return res

    def write(self, vals):
        res = super(sale_order, self).write(vals)
        comm_obj = self.env['sales.commission']
        commission_pay_on = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_pay_on')
        commission_pay_by = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_pay_by')
        if commission_pay_on == 'order_confirm':
            for sale_id in self.filtered(lambda sale: sale.state == 'sale'):
                for commline in sale_id.sale_order_comm_ids:
                    vals = {'name': sale_id.name,
                            'sale_order_id': sale_id.id,
                            'user_id': commline.user_id.id,
                            'commission_date': datetime.today().date(),
                            'amount': commline.commission,
                            'pay_by': commission_pay_by or 'invoice'}
                    comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel')])
                    total_paid_amount = sum(comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                    if total_paid_amount <= commline.commission:
                        vals['amount'] = commline.commission - total_paid_amount
                    comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                    if vals['amount'] != 0.0:
                        comm_obj.create(vals)

        return res

    def _get_commission_calc(self):
        return self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_calc') or ''

    def _get_commission_pay(self):
        return self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_pay_on') or ''

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(sale_order, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                   submenu=submenu)
    #     # if view_type == 'form':
    #     #     if not self.env.user.has_group('sales_team.group_sale_manager'):
    #     #         doc = etree.XML(res['arch'])
    #     #         if doc.xpath("//field[@name='commission_calc']"):
    #     #             node = doc.xpath("//field[@name='commission_calc']")[0]
    #     #             node.set('readonly', '1')
    #     #             setup_modifiers(node, res['fields']['commission_calc'])
    #     #         res['arch'] = etree.tostring(doc)
    #     return res

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.depends('partner_id', 'team_id', 'user_id', 'commission_calc', 'amount_total')
    def _compute_commission_data(self):
        member_lst = []
        commission_pay_on = self.env['ir.config_parameter'].sudo().get_param(
            'aspl_sales_commission_ee.commission_pay_on') or ''
        if self.user_id and commission_pay_on == 'order_confirm':
            emp_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            if emp_id:
                if self.commission_calc == 'product':
                    for soline in self.order_line:
                        for lineid in soline.product_id.product_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                            if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                                lines['commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if self.user_id.id in self.job_related_users(lineid.job_id):
                                    lines[
                                        'commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                    member_lst.append(lines)
                                    break
                elif self.commission_calc == 'product_categ':
                    for soline in self.order_line:
                        for lineid in soline.product_id.categ_id.prod_categ_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                            if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                                lines[
                                    'commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if self.user_id.id in self.job_related_users(lineid.job_id):
                                    lines[
                                        'commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                    member_lst.append(lines)
                                    break
                elif self.commission_calc == 'customer' and self.partner_id:
                    for lineid in self.partner_id.comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                        if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                            lines[
                                'commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                            member_lst.append(lines)
                            break
                        elif lineid.job_id and not lineid.user_ids:
                            if self.user_id.id in self.job_related_users(lineid.job_id):
                                lines[
                                    'commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                member_lst.append(lines)
                                break
                elif self.commission_calc == 'sale_team' and self.team_id:
                    for lineid in self.team_id.sale_team_comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                        if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                            lines[
                                'commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                            member_lst.append(lines)
                            break
                        elif lineid.job_id and not lineid.user_ids:
                            if self.user_id.id in self.job_related_users(lineid.job_id):
                                lines[
                                    'commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                member_lst.append(lines)
                                break
        userby = {}
        for member in member_lst:
            if member['user_id'] in userby:
                userby[member['user_id']]['commission'] += member['commission']
            else:
                userby.update({member['user_id']: member})
        member_lst = []
        for user in userby:
            member_lst.append((0, 0, userby[user]))
        self.sale_order_comm_ids = member_lst



    sale_order_comm_ids = fields.One2many('sales.order.commission', 'order_id', string="Sale Order Commission",
                                          compute="_compute_commission_data", store=True)
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation",
                                       default=_get_commission_calc, copy=False)
    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Commission Pay On",
                                         readonly=True, default=_get_commission_pay, copy=False)
    commission_pay_to = fields.Selection([('users', 'Users'), ('non_users', 'Non User')], default="users",
                                         string="Commission Pay To")
    sales_rep = fields.Many2one('res.partner', string="Sales Rep")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
