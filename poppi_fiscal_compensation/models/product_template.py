# Copyright 2025 - TODAY Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProductTemplate(models.Model):
    """Extend Product Template with Brazilian compensation value."""

    _inherit = "product.template"

    compensation_value = fields.Float(
        default=0.0,
        digits="Product Price",
    )
