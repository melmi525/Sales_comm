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
from odoo.exceptions import Warning


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if res:
            active_obj = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            res.update({'commission_calc': active_obj.commission_calc,
                        'commission_pay_on': active_obj.commission_pay_on,
                        'sales_rep': active_obj.sales_rep,
                        'commission_pay_to': active_obj.commission_pay_to})
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False):
        res = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
        active_obj = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if active_obj:
            res.update({'commission_calc': active_obj.commission_calc,
                        'commission_pay_on': active_obj.commission_pay_on,
                        'sales_rep': active_obj.sales_rep,
                        'commission_pay_to': active_obj.commission_pay_to})
        return res



class account_move(models.Model):
    _inherit = 'account.move'

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False


    commission_invoice = fields.Boolean(string="Commission Invoice" )
    sale_order_comm_ids = fields.One2many('sales.order.commission', 'invoice_id', string="Sale Order Commission",
                                          store=True, readonly=True)
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation", copy=False,
                                       readonly=True)
    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                           ('invoice_pay', 'Customer Invoice Payment')], string="Commission Pay On",
                                         readonly=True, copy=False)
    commission_pay_to = fields.Selection([('users', 'Users'), ('non_users', 'Non User')], default="users",
                                         string="Commission Pay To")
    sales_rep = fields.Many2one('res.partner', string="Sales Rep")


    def post(self):
        res = super(account_move, self).post()
        comm_obj = self.env['sales.commission']
        sale_obj = self.env['sale.order']
        commission_pay_by = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_pay_by')
        member_lst = []
        for each in self:
            if each.commission_calc and each.commission_pay_on == 'invoice_validate':
                emp_id = each.env['hr.employee'].search([('user_id', '=', each.user_id.id)], limit=1)
                sale_id = False
                for invoice in each:
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                if emp_id and sale_id:
                    if each.commission_calc == 'product':
                        for invline in each.invoice_line_ids:
                            for lineid in invline.product_id.product_comm_ids:
                                lines = {'user_id': each.user_id.id,
                                         'job_id': emp_id.job_id.id}
                                if lineid.user_ids and each.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines[
                                        'commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if each.user_id.id in each.job_related_users(lineid.job_id):
                                        lines[
                                            'commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                    elif each.commission_calc == 'product_categ':
                        for invline in each.invoice_line_ids:
                            for lineid in invline.product_id.categ_id.prod_categ_comm_ids:
                                lines = {'user_id': each.user_id.id,
                                         'job_id': emp_id.job_id.id}
                                if lineid.user_ids and each.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines[
                                        'commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if each.user_id.id in each.job_related_users(lineid.job_id):
                                        lines[
                                            'commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                    elif each.commission_calc == 'customer' and each.partner_id:
                        for lineid in each.partner_id.comm_ids:
                            lines = {'user_id': each.user_id.id,
                                     'job_id': emp_id.job_id.id
                                     }
                            if lineid.user_ids and each.user_id.id in [user.id for user in lineid.user_ids]:
                                lines[
                                    'commission'] = each.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (
                                                                                                                                                       lineid.commission * each.amount_total) / sale_id.amount_total
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if each.user_id.id in each.job_related_users(lineid.job_id):
                                    lines[
                                        'commission'] = each.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (
                                                                                                                                                           lineid.commission * each.amount_total) / sale_id.amount_total
                                    member_lst.append(lines)
                                    break
                    elif each.commission_calc == 'sale_team' and each.team_id:
                        for lineid in each.team_id.sale_team_comm_ids:
                            lines = {'user_id': each.user_id.id,
                                     'job_id': emp_id.job_id.id
                                     }
                            if lineid.user_ids and each.user_id.id in [user.id for user in lineid.user_ids]:
                                lines[
                                    'commission'] = each.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (
                                                                                                                                                       lineid.commission * each.amount_total) / sale_id.amount_total
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if each.user_id.id in each.job_related_users(lineid.job_id):
                                    lines[
                                        'commission'] = each.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (
                                                                                                                                                           lineid.commission * each.amount_total) / sale_id.amount_total
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
                each.sale_order_comm_ids = False
                each.sale_order_comm_ids = member_lst

                for invoice in each:
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    tot_amount_paid = sale_id.order_line.filtered(
                        lambda l: l.qty_invoiced and l.product_id.type != 'service')
                    if sale_id and tot_amount_paid:
                        for commline in each.sale_order_comm_ids:
                            vals = {'name': sale_id.name,
                                    'user_id': commline.user_id.id,
                                    'commission_date': datetime.today().date(),
                                    'amount': commline.commission,
                                    'reference_invoice_id': invoice.id,
                                    'sale_order_id': sale_id.id,
                                    'pay_by': commission_pay_by or 'invoice',
                                    'partner_id': sale_id.sales_rep.id if sale_id.commission_pay_to == 'non_user' else False}
                            comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                        ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel'),
                                                        ('reference_invoice_id', '=', invoice.id)])
                            total_paid_amount = sum(
                                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                            if total_paid_amount <= commline.commission:
                                vals['amount'] = commline.commission - total_paid_amount
                            comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                            if vals['amount'] != 0.0:
                                comm_obj.create(vals)

            elif each.commission_calc and each.commission_pay_on == 'invoice_pay' and each.amount_total == 0:
                emp_id = each.env['hr.employee'].search([('user_id', '=', each.user_id.id)], limit=1)
                sale_id = sale_obj.search([('invoice_ids', 'in', [each.id])], limit=1)
                if each.commission_calc == 'customer' and each.partner_id and \
                         each.commission_pay_to == 'users':
                    for lineid in each.partner_id.comm_ids:
                        lines = {'user_id': each.user_id.id,
                                 'job_id': emp_id.job_id.id
                                 }
                        if lineid.user_ids and each.user_id.id in [user.id for user in lineid.user_ids]:
                            lines[ 'commission'] = sale_id.margin * lineid.commission / 100 if \
                                lineid.compute_price_type == 'per' else \
                                (lineid.commission * sale_id.margin) / sale_id.margin
                            member_lst.append(lines)
                            break
                        elif lineid.job_id and not lineid.user_ids:
                            if each.user_id.id in self.job_related_users(lineid.job_id):
                                lines['commission'] = sale_id.margin * lineid.commission / 100 if\
                                    lineid.compute_price_type == 'per' else\
                                    (lineid.commission * sale_id.margin) / sale_id.margin
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
                    each.sale_order_comm_ids = False
                    each.sale_order_comm_ids = member_lst
                elif each.commission_calc == 'customer' and each.partner_id and \
                        each.commission_pay_to == 'non_users':
                    if each.sales_rep:
                        for lineid in each.sales_rep.comm_ids:
                            lines = {'partner_id': each.sales_rep.id}
                            sale_id = sale_obj.search([('invoice_ids', 'in', [each.id])], limit=1)
                            lines['commission'] = sale_id.margin * lineid.commission / 100 if\
                                lineid.compute_price_type == 'per' else \
                                (lineid.commission * sale_id.margin) / sale_id.margin
                            member_lst.append(lines)
                            break
                if each.commission_calc == 'customer' and each.partner_id and \
                        each.commission_pay_to == 'non_users':
                    partnerby = {}
                    for member in member_lst:
                        if member['partner_id'] in partnerby:
                            partnerby[member['partner_id']]['commission'] += member['commission']
                        else:
                            partnerby.update({member['partner_id']: member})
                    member_lst = []
                    for partner in partnerby:
                        member_lst.append((0, 0, partnerby[partner]))
                    each.sale_order_comm_ids = False
                    each.sale_order_comm_ids = member_lst

                for invoice in each:
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    tot_amount_paid = sale_id.order_line.filtered(
                        lambda l: l.qty_invoiced and l.product_id.type != 'service')
                    if sale_id and tot_amount_paid:
                        for commline in each.sale_order_comm_ids:
                            vals = {'name': sale_id.name,
                                    'user_id': commline.user_id.id,
                                    'commission_date': datetime.today().date(),
                                    'amount': commline.commission,
                                    'reference_invoice_id': invoice.id,
                                    'sale_order_id': sale_id.id,
                                    'pay_by': commission_pay_by or 'invoice',
                                    'partner_id': sale_id.sales_rep.id if sale_id.commission_pay_to == 'non_users' else False}
                            comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                        ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel'),
                                                        ('reference_invoice_id', '=', invoice.id)])
                            total_paid_amount = sum(
                                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                            if total_paid_amount <= commline.commission:
                                vals['amount'] = commline.commission - total_paid_amount
                            comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                            if vals['amount'] != 0.0:
                                comm_obj.create(vals)
        return res

    def button_cancel(self):
        res = super(account_move, self).button_cancel()
        comm_obj = self.env['sales.commission']
        for invoice in self:
            if invoice.commission_invoice:

                comm_ids = comm_obj.search([('invoice_id', '=', invoice.id), ('state', 'not in', ['cancel', 'paid'])])
                comm_ids.write({'state': 'draft', 'invoice_id': False})
        return res


    def button_draft(self):
        res = super(account_move, self).button_draft()
        comm_obj = self.env['sales.commission']
        for invoice in self:
            if invoice.commission_invoice:
                for line in invoice.invoice_line_ids.filtered(lambda l: l.sale_commission_id):
                    if line.sale_commission_id.invoice_id:
                        raise Warning(_('Invoice cannot set as a Draft, because related commission lines assign to %s Invoice.') % (line.sale_commission_id.invoice_id.name or 'another'))
                    else:
                        if line.sale_commission_id.state == 'cancel':
                            raise Warning(_('Invoice cannot set as a Draft, because %s commission line is Cancelled.') % (line.sale_commission_id.name))
                        line.sale_commission_id.write({'state': 'invoiced', 'invoice_id': invoice.id})
        return res


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    sale_commission_id = fields.Many2one('sales.commission', string="Sale Commission", readonly=True)

    def unlink(self):
        for line in self.filtered(lambda l:l.sale_commission_id):
            if line.sale_commission_id.invoice_id.id == line.move_id.id:
                line.sale_commission_id.write({'state': 'draft', 'invoice_id': False})
        return super(account_move_line, self).unlink()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    def post(self):
        super(AccountPayment, self).post()
        comm_obj = self.env['sales.commission']
        sale_obj = self.env['sale.order']
        commission_pay_by = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission_ee.commission_pay_by')
        for rec in self:
            for invoice in rec.invoice_ids:
                if invoice.commission_invoice and invoice.state == 'posted':
                    sale_commission = comm_obj.search([('invoice_id', '=', invoice.id)])
                    sale_commission.write({'state': 'paid'})
                elif not invoice.commission_invoice and invoice.commission_pay_on == 'invoice_pay' and invoice.state == 'posted':
                    member_lst = []
                    emp_id = self.env['hr.employee'].search([('user_id', '=', invoice.user_id.id)], limit=1)
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    if emp_id and sale_id:
                        if invoice.commission_calc == 'product':
                            for invline in invoice.invoice_line_ids:
                                for lineid in invline.product_id.product_comm_ids:
                                    lines = {'user_id': invoice.user_id.id,
                                             'job_id': emp_id.job_id.id
                                             }
                                    if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                        lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                                    elif lineid.job_id and not lineid.user_ids:
                                        if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                            lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                            member_lst.append(lines)
                                            break
                        elif invoice.commission_calc == 'product_categ':
                            for invline in invoice.invoice_line_ids:
                                for lineid in invline.product_id.categ_id.prod_categ_comm_ids:
                                    lines = {'user_id': invoice.user_id.id,
                                             'job_id': emp_id.job_id.id
                                             }
                                    if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                        lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                                    elif lineid.job_id and not lineid.user_ids:
                                        if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                            lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                            member_lst.append(lines)
                                            break
                        elif invoice.commission_calc == 'customer' and invoice.partner_id and \
                                invoice.commission_pay_to == 'users':
                            for lineid in invoice.partner_id.comm_ids:
                                lines = {'user_id': invoice.user_id.id,
                                         'job_id': emp_id.job_id.id
                                         }
                                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                                if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines['commission'] = sale_id.margin * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * sale_id.margin) / sale_id.margin
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                        lines['commission'] = sale_id.margin * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * sale_id.margin) / sale_id.margin
                                        member_lst.append(lines)
                                        break
                        elif invoice.commission_calc == 'customer' and invoice.partner_id and \
                                invoice.commission_pay_to == 'non_users':
                            if invoice.sales_rep:
                                for lineid in invoice.sales_rep.comm_ids:
                                    lines = {'partner_id': invoice.sales_rep.id}
                                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                                    lines['commission'] = sale_id.margin * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * sale_id.margin) / sale_id.margin
                                    member_lst.append(lines)
                                    break
                        elif invoice.commission_calc == 'sale_team' and invoice.team_id:
                            for lineid in invoice.team_id.sale_team_comm_ids:
                                lines = {'user_id': invoice.user_id.id,
                                         'job_id': emp_id.job_id.id
                                         }
                                if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                        lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                        member_lst.append(lines)
                                        break

                    if invoice.commission_calc == 'customer' and invoice.partner_id and \
                                invoice.commission_pay_to == 'non_users':
                        partnerby = {}
                        for member in member_lst:
                            if member['partner_id'] in partnerby:
                                partnerby[member['partner_id']]['commission'] += member['commission']
                            else:
                                partnerby.update({member['partner_id']: member})
                        member_lst = []
                        for partner in partnerby:
                            member_lst.append((0, 0, partnerby[partner]))
                        invoice.sale_order_comm_ids = False
                    else:
                        userby = {}
                        for member in member_lst:
                            if member['user_id'] in userby:
                                userby[member['user_id']]['commission'] += member['commission']
                            else:
                                userby.update({member['user_id']: member})
                        member_lst = []
                        for user in userby:
                            member_lst.append((0, 0, userby[user]))
                        invoice.sale_order_comm_ids = False

                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    if sale_id:

                        tot_amount_paid = sale_id.order_line.filtered(lambda l: l.qty_invoiced and l.product_id.type!='service')
                        if tot_amount_paid:
                            if all([inv.state == 'posted' for inv in sale_id.invoice_ids]) and sale_id.invoice_status != 'to invoice':
                                invoice.sale_order_comm_ids = member_lst
                                for commline in invoice.sale_order_comm_ids:
                                    vals = {'name': sale_id.name,
                                            'user_id': commline.user_id.id,
                                            'commission_date': datetime.today().date(),
                                            'amount': commline.commission,
                                            'reference_invoice_id': invoice.id,
                                            'sale_order_id': sale_id.id,
                                            'pay_by': commission_pay_by or 'invoice',
                                            'partner_id': sale_id.sales_rep.id if sale_id.commission_pay_to == 'non_users' else False}
                                    comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                                ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel'),
                                                                ('reference_invoice_id', '=', invoice.id)])
                                    total_paid_amount = sum(comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                                    if total_paid_amount <= commline.commission:
                                        vals['amount'] = commline.commission - total_paid_amount
                                    comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                                    if vals['amount'] != 0.0:
                                        comm_obj.create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: