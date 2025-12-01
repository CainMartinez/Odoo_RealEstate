# -*- coding: utf-8 -*-
{
    'name': 'Real Estate',
    'version': '19.0.1.0.0',
    'summary': 'Real Estate Management',
    'description': """
        Real Estate Module
        ==================
        Manage real estate properties
    """,
    'author': 'Caín Martínez',
    'website': 'https://cain-dev.es',
    'license': 'LGPL-3',
    'category': 'Sales',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}