from odoo import api, fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence, name'

    # SQL constraints
    _sql_constraints = [
        ('unique_property_type_name', 'UNIQUE(name)', 'The property type name must be unique.'),
    ]

    name = fields.Char(string='Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
    offer_ids = fields.One2many('estate.property.offer', 'property_type_id', string='Offers')
    offer_count = fields.Integer(string='Offer Count', compute='_compute_offer_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        """Compute the number of offers for this property type"""
        for record in self:
            record.offer_count = len(record.offer_ids)
