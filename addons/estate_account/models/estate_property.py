# -*- coding: utf-8 -*-

from odoo import Command, models


class EstateProperty(models.Model):
    _inherit = 'estate.property'

    def action_sold(self):
        """Override to create invoice when property is sold"""
        # Call parent method first
        result = super().action_sold()
        
        # Create invoice for each sold property
        for property in self:
            # Create invoice with lines
            self.env['account.move'].create({
                'partner_id': property.buyer_id.id,
                'move_type': 'out_invoice',
                'invoice_line_ids': [
                    # Line 1: 6% of selling price
                    Command.create({
                        'name': 'Property Sale - %s' % property.name,
                        'quantity': 1,
                        'price_unit': property.selling_price * 0.06,
                    }),
                    # Line 2: Administrative fees
                    Command.create({
                        'name': 'Administrative Fees',
                        'quantity': 1,
                        'price_unit': 100.00,
                    }),
                ],
            })
        
        return result
