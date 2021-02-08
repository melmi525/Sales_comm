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


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.constrains('prod_categ_comm_ids', 'prod_categ_comm_ids.commission')
    def _check_commission_values(self):
        if self.prod_categ_comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    prod_categ_comm_ids = fields.One2many('product.categ.commission', 'categ_id', string="Sales Commission")


class ProductCategoryCommission(models.Model):
    _name = 'product.categ.commission'

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
    categ_id = fields.Many2one('product.category', string="Product Category")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.constrains('product_comm_ids', 'product_comm_ids.commission')
    def _check_commission_values(self):
        if self.product_comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    product_comm_ids = fields.One2many('product.commission', 'product_id', string="Sales Commission")


class ProductCommission(models.Model):
    _name = 'product.commission'

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
    product_id = fields.Many2one('product.product', string="Product")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: