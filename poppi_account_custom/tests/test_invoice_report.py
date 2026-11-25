from lxml import html

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceReport(AccountTestInvoicingCommon):
    chart_template = "generic_coa"
    country_code = "US"

    def _render_invoice(self, invoice):
        content, _format = self.env["ir.actions.report"]._render_qweb_html(
            "account.report_invoice", invoice.ids
        )
        return html.fromstring(content)

    def test_installments_share_one_invoice_article(self):
        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Two installments",
                "display_on_invoice": True,
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 50, "nb_days": 30}
                    ),
                    Command.create(
                        {"value": "percent", "value_amount": 50, "nb_days": 60}
                    ),
                ],
            }
        )
        fiscal_document = (
            self.env["l10n_br_fiscal.document"]
            .sudo()
            .create(
                {
                    "company_id": self.env.company.id,
                    "partner_id": self.partner_a.id,
                    "document_number": "321654",
                }
            )
        )
        invoice = self._create_invoice_one_line(
            invoice_date="2026-01-05",
            price_unit=100,
            product_id=self.product_a,
            tax_ids=self.tax_sale_a,
            invoice_payment_term_id=payment_term,
            fiscal_document_id=fiscal_document,
        )
        invoice.invalidate_recordset(["fiscal_document_id", "document_number"])
        report = self._render_invoice(invoice)
        articles = report.xpath(
            f"//div[@data-oe-model='account.move'][@data-oe-id='{invoice.id}']"
        )
        self.assertEqual(len(articles), 1)

        pages = articles[0].xpath(".//div[table[@name='installments_table']]")
        self.assertEqual(len(pages), 2)
        for index, page in enumerate(pages, 1):
            with self.subTest(installment=index):
                installment = f"{index} / 2"
                title = page.xpath("string(h2[@name='poppi_installment_title'])")
                self.assertIn(installment, " ".join(title.split()))
                rows = page.xpath("table[@name='installments_table']/tbody/tr")
                self.assertEqual(len(rows), 2)
                self.assertEqual(
                    [row for row in rows if row.get("style")], [rows[index - 1]]
                )
                number, date, _amount = rows[index - 1]
                self.assertIn(installment, " ".join(number.text_content().split()))
                due_date = page.xpath("string(.//div[@name='poppi_due_date']/div)")
                self.assertEqual(due_date.strip(), date.text_content().strip())
                self.assertEqual(
                    page.xpath("string(div[@name='poppi_document_number']/h3/span[2])"),
                    "321654",
                )
                self.assertFalse(
                    page.xpath(
                        ".//div[@id='total_payment_term_details_table']//div/div"
                    )
                )
                self.assertFalse(page.xpath(".//th[@name='th_taxes']"))
                self.assertFalse(page.xpath(".//*[@id='line_tax_ids']"))
                self.assertFalse(page.xpath(".//tr[@class='o_taxes']"))
                self.assertTrue(page.xpath(".//tr[@class='o_total']"))

    def test_draft_without_payment_lines_keeps_invoice_report(self):
        invoice = self._create_invoice(invoice_line_ids=[])
        report = self._render_invoice(invoice)
        self.assertTrue(report.xpath("//table[@name='invoice_line_table']"))
        self.assertFalse(report.xpath("//table[@name='installments_table']"))
