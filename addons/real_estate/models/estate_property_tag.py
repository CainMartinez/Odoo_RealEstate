# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class EstatePropertyTag(models.Model):
    # Private attributes
    _name = 'estate.property.tag'
    _description = 'Real Estate Property Tag'
    _order = 'name'

    # Fields
    name = fields.Char(string='Tag', required=True)
    color = fields.Integer(string='Color')

    # SQL constraints
    _sql_constraints = [
        ('unique_property_tag_name', 'UNIQUE(name)', 'The property tag name must be unique.'),
    ]
