# Copyright 2026 MarcusPDL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import html

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPoppiDelivery(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Poppi Test Recipient", "legal_name": "Poppi Test Recipient"}
        )
        order = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        group = cls.env["procurement.group"].create(
            {"name": "Poppi Test Delivery", "sale_id": order.id}
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )
        product = cls.env.ref("product.product_product_4")
        cls.env["stock.move"].create(
            {
                "name": "Poppi Test Move",
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": 1,
                "picking_id": cls.picking.id,
                "group_id": group.id,
                "location_id": cls.picking.location_id.id,
                "location_dest_id": cls.picking.location_dest_id.id,
            }
        )

    def _render(self, template):
        result = self.env["ir.actions.report"]._render_template(
            f"poppi_delivery_custom.report_poppi_delivery_{template}",
            {"o": self.picking},
        )
        return html.fromstring(result)

    def test_reports_without_invoice(self):
        """A delivery without an invoice still produces both documents."""
        for template in ("label", "document"):
            report = self._render(template)
            self.assertEqual(len(report.xpath("//div[@class='page']")), 1)
            self.assertIn(self.partner.name, report.text_content())

    def test_reshipment_onchange(self):
        order = self.env["sale.order"].new(
            {
                "partner_id": self.partner.id,
                "reshipment_partner_id": self.partner.id,
                "reshipment_payment": "customer",
            }
        )
        order.onchange_sale_order_carrier_id()
        self.assertFalse(order.reshipment_partner_id)
        self.assertFalse(order.reshipment_payment)

    def test_labels_for_multiple_volumes(self):
        """Each volume group prints its quantity; extra invoices remain safe."""
        self.env["spec.mixin.nfe"].with_context(
            spec_schema="nfe", spec_version="40"
        )._register_hook()
        document = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        document.nfe40_vol = [
            Command.clear(),
            Command.create({"nfe40_qVol": "2", "nfe40_esp": "BOX-A"}),
            Command.create({"nfe40_qVol": "3", "nfe40_esp": "BOX-B"}),
        ]
        invoices = self.env["account.move"].new(
            {"fiscal_document_id": document.id}
        ) | self.env["account.move"].new({"fiscal_document_id": document.id})
        self.picking = self.picking.new(self.picking.copy_data()[0])
        self.picking.invoice_ids = invoices
        report = self._render("label")
        self.assertEqual(len(report.xpath("//div[@class='page']")), 5)
        report = self._render("document")
        self.assertIn("BOX-A", report.text_content())
        self.assertIn("BOX-B", report.text_content())
