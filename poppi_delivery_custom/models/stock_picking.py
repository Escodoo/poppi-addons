# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    reshipment_partner_id = fields.Many2one(
        "res.partner",
        related="sale_id.reshipment_partner_id",
        readonly=True
    )
    reshipment_payment = fields.Selection(
        related="sale_id.reshipment_payment",
        readonly=True
    )
