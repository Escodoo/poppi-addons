# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaPoppi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.l10n_br_company = cls.env["res.company"].create(
            {
                "name": "Empresa Teste do Plano de Contas",
                "currency_id": cls.env.ref("base.BRL").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.env["account.chart.template"].try_loading(
            "br_poppi", cls.l10n_br_company, install_demo=False
        )

    def _account(self, code):
        return (
            self.env["account.account"]
            .with_company(self.l10n_br_company)
            .search([("code", "=", code)])
        )

    def test_l10n_br_coa_poppi(self):
        """Test installing the chart of accounts template in a new company"""
        company = self.l10n_br_company
        self.assertEqual(company.chart_template, "br_poppi")
        self.assertTrue(company.anglo_saxon_accounting)
        self.assertEqual(company.cash_account_code_prefix, "111.01.")
        self.assertEqual(company.bank_account_code_prefix, "111.02.")
        partner_receivable = (
            self.env["res.partner"]
            .with_company(company)
            .create({"name": "Cliente Teste"})
            .property_account_receivable_id
        )
        self.assertEqual(partner_receivable.code, "112.01.01")

    def test_tax_group_accounts(self):
        """PIS sale tax uses the Poppi accounts instead of the generic ones"""
        tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.l10n_br_company.id),
                ("type_tax_use", "=", "sale"),
                ("deductible", "=", False),
                ("withholdable", "=", False),
                ("tax_group_id.name", "=", "PIS"),
            ],
            limit=1,
        )
        self.assertTrue(tax)
        inv_line = tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        ref_line = tax.refund_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertEqual(inv_line.account_id, self._account("211.05.23"))
        self.assertEqual(ref_line.account_id, self._account("112.07.06"))
