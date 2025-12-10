# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class EstateProperty(models.Model):
    # Private attributes
    _inherit = 'estate.property'

    # Business methods
    def action_sold(self):
        """Override to create invoice when property is sold"""
        result = super().action_sold()
        
        # Create invoice for the sold property
        AccountMove = self.env['account.move']
        for prop in self:
            AccountMove.create({
                'partner_id': prop.buyer_id.id,
                'move_type': 'out_invoice',
                'invoice_line_ids': [
                    (0, 0, {
                        'name': 'Property Sale - %s' % prop.name,
                        'quantity': 1,
                        'price_unit': prop.selling_price * 0.06,
                    }),
                    (0, 0, {
                        'name': 'Administrative Fees',
                        'quantity': 1,
                        'price_unit': 100.00,
                    }),
                ],
            })
        
        return result
