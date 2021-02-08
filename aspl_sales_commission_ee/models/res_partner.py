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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('comm_ids', 'comm_ids.commission')
    def _check_commission_values(self):
        if self.comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    comm_ids = fields.One2many('res.partner.commission', 'partner_id', string="Sales Commission")
    sales_rep = fields.Boolean(string="Sales Rep")


class ResPartnerCommission(models.Model):
    _name = 'res.partner.commission'

    @api.onchange('job_id')
    def onchange_job_id(self):
        self.user_ids = False

    @api.onchange('commission', 'compute_price_type')
    def onchange_commission(self):
        if self.commission and self.compute_price_type == 'per' and (self.commission < 0.0 or self.commission > 100):
            raise Warning(_('Entered Commission is %s. \n Commission value for Percentage type must be between 0 to 100. ') % self.commission)

    job_id = fields.Many2one('hr.job', string="Job Position")
    user_ids = fields.Many2many('res.users', string="User(s)")
    compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                          string="Compute Price", default="per", required=True)
    commission = fields.Float(string="Commission")
    partner_id = fields.Many2one('res.partner', string="Partner")


class res_users(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('ctx_job_id'):
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False),
                                                      ('job_id', '=', self._context['ctx_job_id'])])
            args += [('id', 'in', [emp.user_id.id for emp in emp_ids])]
        return super(res_users, self).name_search(name=name, args=args, operator='ilike', limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: