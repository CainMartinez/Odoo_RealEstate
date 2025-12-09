# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"

    # SQL constraints
    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)', 'The expected price must be strictly positive.'),
        ('check_selling_price', 'CHECK(selling_price >= 0)', 'The selling price must be positive.'),
    ]

    # Basic fields
    name = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(
        string="Available From",
        copy=False,
        default=lambda self: fields.Date.today() + relativedelta(months=3)
    )
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price", readonly=True, copy=False)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer(string="Facades")
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        help="Garden orientation"
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        string="Status",
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled')
        ],
        required=True,
        copy=False,
        default='new'
    )

    # Computed fields
    total_area = fields.Integer(string="Total Area (sqm)", compute="_compute_total_area")
    best_price = fields.Float(string="Best Offer", compute="_compute_best_price")

    # Relational fields
    property_type_id = fields.Many2one('estate.property.type', string='Property Type')
    buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False)
    seller_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    tag_ids = fields.Many2many('estate.property.tag', string='Tags')
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Offers')

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        """Compute total area as sum of living area and garden area"""
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        """Compute best price as the maximum offer price"""
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price')) if record.offer_ids else 0.0

    @api.onchange('garden')
    def _onchange_garden(self):
        """Set default values for garden area and orientation when garden is enabled"""
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = None

    def action_cancel(self):
        """Cancel the property"""
        for record in self:
            if record.state == 'sold':
                raise UserError("Sold properties cannot be cancelled.")
            record.state = 'canceled'
        return True

    def action_sold(self):
        """Mark the property as sold"""
        for record in self:
            if record.state == 'canceled':
                raise UserError("Canceled properties cannot be sold.")
            record.state = 'sold'
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_new_or_canceled(self):
        """Prevent deletion of properties that are not new or cancelled"""
        for record in self:
            if record.state not in ('new', 'canceled'):
                raise UserError("Only new and cancelled properties can be deleted.")

    @api.constrains('expected_price')
    def _check_expected_price(self):
        """Validate that expected price is strictly positive"""
        for record in self:
            if float_compare(record.expected_price, 0, precision_digits=2) <= 0:
                raise ValidationError("The expected price must be strictly positive.")

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        """Validate that selling price is at least 90% of expected price"""
        for record in self:
            # Only check if selling_price is set (i.e., property has been sold)
            if not float_is_zero(record.selling_price, precision_digits=2):
                min_price = record.expected_price * 0.9
                if float_compare(record.selling_price, min_price, precision_digits=2) < 0:
                    raise ValidationError(
                        "The selling price cannot be lower than 90%% of the expected price. "
                        "Expected: %.2f, Minimum allowed: %.2f, Got: %.2f" % 
                        (record.expected_price, min_price, record.selling_price)
                    )
