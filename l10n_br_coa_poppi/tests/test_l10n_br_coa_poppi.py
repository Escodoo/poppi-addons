# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaPoppi(TransactionCase):
    def setUp(self):
        super(L10nBrCoaPoppi, self).setUp()

        self.l10n_br_coa_poppi = self.env.ref(
            "l10n_br_coa_poppi.l10n_br_coa_poppi_chart_template"
        )
        self.l10n_br_company = self.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas"}
        )

    def test_l10n_br_coa_poppi(self):
        """Test installing the chart of accounts template in a new company"""
        self.l10n_br_coa_poppi.try_loading(company=self.l10n_br_company)
        self.assertEqual(self.l10n_br_coa_poppi, self.l10n_br_company.chart_template_id)
