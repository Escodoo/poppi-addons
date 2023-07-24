# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    reshipment_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Reshipment Partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    reshipment_payment = fields.Selection(
        [("customer", "Customer"), ("company", "Company")],
        string="Reshipment Payment",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("carrier_id")
    def onchange_sale_order_carrier_id(self):
        if not self.carrier_id:
            self.reshipment_partner_id = False
            self.reshipment_payment = False
