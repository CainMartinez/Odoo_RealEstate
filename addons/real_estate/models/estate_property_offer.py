from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Real Estate Property Offer'
    _order = 'price desc'

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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set property state to offer_received"""
        offers = super().create(vals_list)
        for offer in offers:
            if offer.property_id.state == 'new':
                offer.property_id.state = 'offer_received'
        return offers

    def action_accept(self):
        """Accept the offer"""
        for record in self:
            # Ensure only one offer is accepted per property
            if record.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != record.id):
                raise UserError("Only one offer can be accepted for a property.")
            record.status = 'accepted'
            # Set buyer and selling price on the property
            record.property_id.buyer_id = record.partner_id
            record.property_id.selling_price = record.price
            record.property_id.state = 'offer_accepted'
        return True

    def action_refuse(self):
        """Refuse the offer"""
        for record in self:
            was_accepted = record.status == 'accepted'
            record.status = 'refused'
            # If the refused offer was accepted, reset property state to offer_received
            if was_accepted:
                record.property_id.state = 'offer_received'
                record.property_id.buyer_id = False
                record.property_id.selling_price = 0
        return True

    def unlink(self):
        """When an offer is deleted, reset the related property's state and selling price.

        The requirement: if the offer is deleted the property must go back to 'new'
        and `selling_price` must be 0 (also clear `buyer_id`).
        """
        for offer in self:
            prop = offer.property_id
            if prop:
                prop.state = 'new'
                prop.selling_price = 0
                prop.buyer_id = False
        return super(EstatePropertyOffer, self).unlink()
