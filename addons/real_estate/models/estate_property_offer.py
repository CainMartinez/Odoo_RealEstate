# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    # Private attributes
    _name = 'estate.property.offer'
    _description = 'Real Estate Property Offer'
    _order = 'price desc'

    # Fields
    price = fields.Float(string='Price')
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        string='Status',
        copy=False
    )
    validity = fields.Integer(string='Validity (days)', default=7)
    date_deadline = fields.Date(string='Deadline', compute='_compute_date_deadline', inverse='_inverse_date_deadline')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)
    property_type_id = fields.Many2one('estate.property.type', related='property_id.property_type_id', string='Property Type', store=True)

    # SQL constraints
    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)', 'The offer price must be strictly positive.'),
    ]

    # Compute and inverse methods
    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        """Compute deadline as create_date + validity days"""
        for record in self:
            # Use create_date if available, otherwise use today
            create_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = create_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        """Set validity based on deadline"""
        for record in self:
            # Use create_date if available, otherwise use today
            create_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.validity = (record.date_deadline - create_date).days

    # CRUD methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set property state to offer_received and validate offer price"""
        # Validate offer prices before creation
        for vals in vals_list:
            property_id = vals.get('property_id')
            if property_id:
                property_obj = self.env['estate.property'].browse(property_id)
                offer_price = vals.get('price', 0)
                # Check if there are existing offers with higher prices
                existing_offers = property_obj.offer_ids
                if existing_offers:
                    max_offer = max(existing_offers.mapped('price'))
                    if offer_price <= max_offer:
                        raise UserError(
                            _("The offer price (%.2f) must be higher than the existing offers (%.2f).") % 
                            (offer_price, max_offer)
                        )
        
        offers = super().create(vals_list)
        for offer in offers:
            if offer.property_id.state == 'new':
                offer.property_id.state = 'offer_received'
        return offers

    def unlink(self):
        """When an offer is deleted, reset the related property's state and selling price"""
        for offer in self:
            prop = offer.property_id
            if prop:
                prop.state = 'new'
                prop.selling_price = 0
                prop.buyer_id = False
        return super(EstatePropertyOffer, self).unlink()

    # Action methods
    def action_accept(self):
        """Accept the offer and update property"""
        self.ensure_one()
        # Ensure only one offer is accepted per property
        if self.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != self.id):
            raise UserError(_("Only one offer can be accepted for a property."))
        
        self.status = 'accepted'
        self.property_id.write({
            'buyer_id': self.partner_id.id,
            'selling_price': self.price,
            'state': 'offer_accepted',
        })
        return True

    def action_refuse(self):
        """Refuse the offer and update property if necessary"""
        self.ensure_one()
        was_accepted = self.status == 'accepted'
        self.status = 'refused'
        
        # If the refused offer was accepted, reset property state
        if was_accepted:
            self.property_id.write({
                'state': 'offer_received',
                'buyer_id': False,
                'selling_price': 0,
            })
        return True
