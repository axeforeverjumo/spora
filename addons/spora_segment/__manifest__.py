{
    'name': 'Spora - Hierarchical Budget Segments',
    'version': '18.0.1.2.0',
    'category': 'Sales',
    'summary': 'Hierarchical budget segments with outline numbering and print reports',
    'description': """
        Adds hierarchical segment structure to sale orders
        with automatic level calculation, outline numbering,
        depth validation, and professional print reports.
    """,
    'author': 'Spora',
    'depends': [
        'sale',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/segment_security.xml',
        'views/sale_order_segment_views.xml',
        'views/sale_order_views.xml',
        'views/project_task_views.xml',
        'report/sale_order_segment_report.xml',
        'report/sale_order_segment_template.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
