{
    'name': 'Spora - Hierarchical Budget Segments',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Hierarchical budget segments for sale orders',
    'description': """
        Adds hierarchical segment structure to sale orders
        with automatic level calculation and depth validation.
    """,
    'author': 'Spora',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_segment_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
