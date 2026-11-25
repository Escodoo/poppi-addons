# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestDifal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
                "name": "DIFAL Test Company",
                "currency_id": cls.env.ref("base.BRL").id,
                "icms_regulation_id": cls.env.ref(
                    "l10n_br_fiscal.tax_icms_regulation"
                ).id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "DIFAL consumer",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_mg").id,
                "ind_ie_dest": "9",
            }
        )
        cls.ncm = cls.env.ref("l10n_br_fiscal.ncm_72132000")
        cls.product = cls.env["product.product"].create(
            {"name": "DIFAL product", "ncm_id": cls.ncm.id}
        )
        cls.operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_venda_venda_nao_contribuinte"
        )
        cls.icms = cls.env.ref("l10n_br_fiscal.tax_icms_12")

    def _compute_taxes(self, operation_line, cfop, taxes=None, price=100.0):
        return (self.icms if taxes is None else taxes).compute_taxes(
            company=self.company,
            partner=self.partner,
            product=self.product,
            price_unit=price,
            quantity=1.0,
            fiscal_price=price,
            fiscal_quantity=1.0,
            ncm=self.ncm,
            nbm=self.product.nbm_id,
            cest=self.product.cest_id,
            uom_id=self.product.uom_id,
            uot_id=self.product.uom_id,
            operation_line=operation_line,
            cfop=self.env.ref(f"l10n_br_fiscal.cfop_{cfop}"),
            ind_final="1",
            icms_cst_id=self.env.ref("l10n_br_fiscal.cst_icms_00"),
        )["taxes"]

    def test_interstate_sale_uses_single_base(self):
        icms = self._compute_taxes(self.operation_line, "6107")["icms"]
        self.assertEqual(icms["tax_value"], 12.0)
        self.assertEqual(icms["icms_dest_perc"], 18.0)
        self.assertEqual(icms["icms_dest_base"], 100.0)
        self.assertEqual(icms["icms_dest_value"], 6.0)
        self.assertEqual(icms["icms_origin_value"], 0.0)

    def test_same_state_sale_does_not_compute_difal(self):
        self.partner.state_id = self.company.state_id
        icms = self._compute_taxes(self.operation_line, "5101")["icms"]
        self.assertEqual(icms["tax_value"], 12.0)
        self.assertEqual(icms["icms_dest_base"], 0.0)
        self.assertEqual(icms["icms_dest_value"], 0.0)

    def _create_incoming_operation(self, fiscal_type):
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "name": f"DIFAL {fiscal_type}",
                "code": f"DIFAL_{fiscal_type.upper()}",
                "fiscal_operation_type": "in",
                "fiscal_type": fiscal_type,
            }
        )
        return self.env["l10n_br_fiscal.operation.line"].create(
            {"name": operation.name, "fiscal_operation_id": operation.id}
        )

    def test_incoming_return_does_not_compute_difal(self):
        operation_line = self._create_incoming_operation("return_in")
        icms = self._compute_taxes(operation_line, "2201")["icms"]
        self.assertEqual(icms["tax_value"], 12.0)
        self.assertEqual(icms["icms_dest_base"], 0.0)
        self.assertEqual(icms["icms_dest_value"], 0.0)

    def test_single_base_in_all_brazilian_states(self):
        brazil = self.env.ref("base.br")
        sao_paulo = self.env.ref("base.state_br_sp")
        rio_de_janeiro = self.env.ref("base.state_br_rj")
        states = self.env["res.country.state"].search([("country_id", "=", brazil.id)])
        self.assertEqual(len(states), 27)
        interstate_icms = self.env.ref("l10n_br_fiscal.tax_icms_4")
        for state in states:
            with self.subTest(uf=state.code):
                self.company.state_id = (
                    rio_de_janeiro if state == sao_paulo else sao_paulo
                )
                self.partner.state_id = state
                icms = self._compute_taxes(
                    self.operation_line, "6107", taxes=interstate_icms
                )["icms"]
                self.assertEqual(icms["tax_value"], 4.0)
                self.assertGreater(icms["icms_dest_perc"], 4.0)
                self.assertEqual(icms["icms_dest_base"], 100.0)
                self.assertAlmostEqual(
                    icms["icms_dest_value"], icms["icms_dest_perc"] - 4.0, places=2
                )
                self.assertEqual(icms["icms_origin_value"], 0.0)

    def test_interstate_taxpayer_does_not_compute_difal(self):
        self.partner.ind_ie_dest = "1"
        sale = self.env.ref("l10n_br_fiscal.fo_venda_venda")
        icms = self._compute_taxes(sale, "6101")["icms"]
        self.assertEqual(icms["tax_value"], 12.0)
        self.assertEqual(icms["icms_dest_base"], 0.0)
        self.assertEqual(icms["icms_dest_value"], 0.0)

    def test_zero_icms_does_not_compute_difal(self):
        exempt_icms = self.env.ref("l10n_br_fiscal.tax_icms_nt")
        icms = self._compute_taxes(self.operation_line, "6107", taxes=exempt_icms)[
            "icms"
        ]
        self.assertEqual(icms["tax_value"], 0.0)
        self.assertEqual(icms["icms_dest_base"], 0.0)
        self.assertEqual(icms["icms_dest_value"], 0.0)

    def test_incoming_purchase_uses_single_base(self):
        operation_line = self._create_incoming_operation("purchase")
        icms = self._compute_taxes(operation_line, "2101")["icms"]
        self.assertEqual(icms["tax_value"], 12.0)
        self.assertEqual(icms["icms_dest_perc"], 18.0)
        self.assertEqual(icms["icms_dest_base"], 100.0)
        self.assertEqual(icms["icms_dest_value"], 6.0)

    def test_fractional_amount_with_fcp(self):
        fcp = self.env.ref("l10n_br_fiscal.tax_icmsfcp_2")
        taxes = self._compute_taxes(
            self.operation_line, "6107", taxes=self.icms | fcp, price=103.37
        )
        self.assertEqual(taxes["icms"]["tax_value"], 12.4)
        self.assertEqual(taxes["icms"]["icms_dest_base"], 103.37)
        self.assertEqual(taxes["icms"]["icms_dest_value"], 6.21)
        self.assertEqual(taxes["icmsfcp"]["base"], 103.37)
        self.assertEqual(taxes["icmsfcp"]["tax_value"], 2.07)
