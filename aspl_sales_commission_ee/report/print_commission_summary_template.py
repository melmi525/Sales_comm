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

from odoo import models, api, _


class print_commission_summary_template(models.AbstractModel):
    _name = 'report.aspl_sales_commission_ee.print_commission_template'



    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('aspl_sales_commission_ee.print_commission_summary_template')
        return {'doc_ids': self.env['wizard.commission.summary'].search([('id', 'in', list(data["ids"]))]),
                'doc_model': report.model,
                'docs': self,
                'data': data,
                'get_sorted_summary': self._get_sorted_summary}

    def _get_sorted_summary(self, summary):
        return sorted(summary.items(), key=lambda item: item[1], reverse=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: