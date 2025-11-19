# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestFiscalCompensation(TransactionCase):
    """Test Fiscal Compensation functionality with off-balance sheet accounts."""

    def setUp(self):  # Changed from setUpClass(cls) to setUp(self)
        """Set up test data for fiscal compensation tests.

        Creates:
        - Off-balance sheet account types and accounts
        - Test journals (sales and compensation)
        - Demo CFOP configurations
        - Test partner and product with compensation values
        """
        # Use super().setUp() instead of super().setUpClass()
        super().setUp()

        # Get company - Use self instead of cls
        self.company = self.env.company

        # Get demo CFOP
        self.cfop_5101 = self.env.ref("l10n_br_fiscal.cfop_5101")
        self.cfop_5102 = self.env.ref("l10n_br_fiscal.cfop_5102")

        # Get or create account types for off-balance sheet accounts
        AccountType = self.env["account.account.type"]

        self.account_type_asset_offset = AccountType.search(
            [("type", "=", "other"), ("name", "ilike", "off-balance")], limit=1
        )

        self.account_type_asset_offset = AccountType.create(
            {
                "name": "Off-Balance Sheet Asset",
                "type": "other",
                "internal_group": "off_balance",
            }
        )

        self.account_type_liability_offset = AccountType.search(
            [("type", "=", "other"), ("name", "ilike", "off-balance")], limit=1
        )

        self.account_type_liability_offset = AccountType.create(
            {
                "name": "Off-Balance Sheet Liability",
                "type": "other",
                "internal_group": "off_balance",
            }
        )

        # Get standard account types
        self.account_type_receivable = self.env.ref(
            "account.data_account_type_receivable"
        )
        self.account_type_revenue = self.env.ref("account.data_account_type_revenue")

        # Create off-balance sheet accounts for compensation
        self.account_asset = self.env["account.account"].create(
            {
                "name": "Goods in Transit - Off-Balance (Test)",
                "code": "9.01.01.01.0001",
                "user_type_id": self.account_type_asset_offset.id,
                "company_id": self.company.id,
                "reconcile": False,
            }
        )

        self.account_liability = self.env["account.account"].create(
            {
                "name": "Compensation Payable - Off-Balance (Test)",
                "code": "9.02.01.01.0001",
                "user_type_id": self.account_type_liability_offset.id,
                "company_id": self.company.id,
                "reconcile": False,
            }
        )

        # Create standard accounts
        self.account_receivable = self.env["account.account"].create(
            {
                "name": "Account Receivable - Test",
                "code": "1.01.02.01.0001",
                "user_type_id": self.account_type_receivable.id,
                "reconcile": True,
                "company_id": self.company.id,
            }
        )

        self.account_revenue = self.env["account.account"].create(
            {
                "name": "Revenue - Test",
                "code": "3.01.01.01.0001",
                "user_type_id": self.account_type_revenue.id,
                "company_id": self.company.id,
            }
        )

        # Create journal for compensation (general type for off-balance entries)
        self.compensation_journal = self.env["account.journal"].create(
            {
                "name": "Compensation Journal - Test",
                "code": "COMP",
                "type": "general",
                "company_id": self.company.id,
            }
        )

        # Create sales journal
        self.sales_journal = self.env["account.journal"].create(
            {
                "name": "Sales Journal - Test",
                "code": "SAL",
                "type": "sale",
                "company_id": self.company.id,
            }
        )

        # Configure CFOP 5101 for compensation with off-balance accounts
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_account_asset": self.account_asset.id,
                "compensation_account_liability": self.account_liability.id,
                "compensation_journal_id": self.compensation_journal.id,
                "compensation_debit_account_type": "asset",
            }
        )

        # Ensure CFOP 5102 has compensation disabled
        self.cfop_5102.write({"use_compensation": False})

        # Create partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer - Fiscal Compensation",
                "property_account_receivable_id": self.account_receivable.id,
            }
        )

        # Create product with compensation value
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product with Compensation",
                "type": "product",
                "standard_price": 100.00,
                "list_price": 150.00,
                "compensation_value": 120.00,
            }
        )

    def _create_invoice(self, cfop, product=None, quantity=1.0):
        """Helper method to create an invoice with fiscal configuration.

        :param cfop: CFOP record to use in invoice line
        :param product: Product record (uses self.product if None)
        :param quantity: Quantity for the invoice line
        :return: Created invoice record in draft state
        """
        if product is None:
            product = self.product

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.sales_journal.id,
                "invoice_date": "2025-01-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": quantity,
                            "price_unit": product.list_price,
                            "account_id": self.account_revenue.id,
                            "cfop_id": cfop.id,
                            "name": product.name,
                        },
                    )
                ],
            }
        )
        return invoice

    def _get_compensation_move(self):
        """Helper method to retrieve the most recent compensation move.

        :return: Account move record or empty recordset
        """
        return self.env["account.move"].search(
            [
                ("ref", "ilike", "Compensation for"),
                ("journal_id", "=", self.compensation_journal.id),
            ],
            order="create_date desc",
            limit=1,
        )

    def test_01_compensation_not_created_when_disabled(self):
        """Test that compensation is not created when use_compensation is False.

        Validates:
        - No compensation move is created when CFOP has use_compensation=False
        - Invoice can be posted normally without compensation
        """
        # Ensure compensation is disabled on CFOP
        self.cfop_5101.use_compensation = False

        invoice = self._create_invoice(self.cfop_5101, quantity=10.0)

        # Get initial compensation move count
        initial_move_count = self.env["account.move"].search_count(
            [("journal_id", "=", self.compensation_journal.id)]
        )

        # Post invoice
        invoice.action_post()

        # Get final compensation move count
        final_move_count = self.env["account.move"].search_count(
            [("journal_id", "=", self.compensation_journal.id)]
        )

        # Should not create any compensation move
        self.assertEqual(
            final_move_count,
            initial_move_count,
            "No compensation move should be created when use_compensation is False",
        )

    def test_02_compensation_created_with_cost_source(self):
        """Test compensation entry creation using product cost as value source.

        Validates:
        - Compensation move is created and posted
        - Debit amount equals quantity × product standard_price
        - Credit amount equals debit amount (balanced entry)
        - Correct off-balance accounts are used
        """
        # Configure CFOP to use cost
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_debit_account_type": "asset",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, quantity=10.0)
        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        self.assertTrue(compensation_move, "Compensation move should be created")
        self.assertEqual(
            compensation_move.state, "posted", "Compensation move should be posted"
        )

        # Expected amount: 10 units * 100.00 cost = 1000.00
        expected_amount = 1000.00

        # Check debit line (off-balance asset account)
        debit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset
        )
        self.assertEqual(
            len(debit_line),
            1,
            "Should have one debit line on off-balance asset account",
        )
        self.assertAlmostEqual(
            debit_line.debit,
            expected_amount,
            places=2,
            msg="Debit amount should match expected value",
        )
        self.assertEqual(debit_line.credit, 0.0, "Debit line should have zero credit")

        # Check credit line (off-balance liability account)
        credit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_liability
        )
        self.assertEqual(
            len(credit_line),
            1,
            "Should have one credit line on off-balance liability account",
        )
        self.assertEqual(credit_line.debit, 0.0, "Credit line should have zero debit")
        self.assertAlmostEqual(
            credit_line.credit,
            expected_amount,
            places=2,
            msg="Credit amount should match expected value",
        )

    def test_03_compensation_created_with_sale_price_source(self):
        """Test compensation entry creation using sale price as value source.

        Validates:
        - Debit amount equals quantity × invoice line price_unit
        - Compensation uses sale price instead of cost
        """
        # Configure CFOP to use sale price
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "sale_price",
                "compensation_debit_account_type": "asset",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, quantity=5.0)
        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        self.assertTrue(compensation_move, "Compensation move should be created")

        # Expected amount: 5 units * 150.00 sale price = 750.00
        expected_amount = 750.00

        debit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset
        )
        self.assertAlmostEqual(
            debit_line.debit,
            expected_amount,
            places=2,
            msg="Debit should use sale price as source",
        )

    def test_04_compensation_created_with_compensation_value_source(self):
        """Test compensation entry creation using product compensation value.

        Validates:
        - Debit amount equals quantity × product.compensation_value
        - Uses product-specific compensation value field
        """
        # Configure CFOP to use compensation value
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "compensation_value",
                "compensation_debit_account_type": "asset",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, quantity=8.0)
        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        self.assertTrue(compensation_move, "Compensation move should be created")

        # Expected amount: 8 units * 120.00 compensation value = 960.00
        expected_amount = 960.00

        debit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset
        )
        self.assertAlmostEqual(
            debit_line.debit,
            expected_amount,
            places=2,
            msg="Debit should use product compensation value as source",
        )

    def test_05_compensation_with_liability_debit_type(self):
        """Test compensation with liability as debit account type (inverted entries).

        Validates:
        - When debit_account_type='liability', accounts are inverted
        - Debit goes to liability account
        - Credit goes to asset account
        - Amount calculation remains correct
        """
        # Configure CFOP to debit off-balance liability account
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_debit_account_type": "liability",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, quantity=10.0)
        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        expected_amount = 1000.00

        # Check debit line (off-balance liability account - inverted)
        debit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_liability
        )
        self.assertEqual(
            len(debit_line),
            1,
            "Should have one debit line on off-balance liability account",
        )
        self.assertAlmostEqual(
            debit_line.debit,
            expected_amount,
            places=2,
            msg="Debit on liability account when inverted",
        )

        # Check credit line (off-balance asset account - inverted)
        credit_line = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset
        )
        self.assertEqual(
            len(credit_line),
            1,
            "Should have one credit line on off-balance asset account",
        )
        self.assertAlmostEqual(
            credit_line.credit,
            expected_amount,
            places=2,
            msg="Credit on asset account when inverted",
        )

    def test_06_no_compensation_for_zero_amount(self):
        """Test that no compensation is created when amount is zero.

        Validates:
        - Products with zero cost/value don't generate compensation
        - System skips zero-value compensation entries
        - No unnecessary journal entries are created
        """
        # Create product with zero cost
        zero_cost_product = self.env["product.product"].create(
            {
                "name": "Zero Cost Product",
                "type": "product",
                "standard_price": 0.0,
                "list_price": 100.0,
                "compensation_value": 0.0,
            }
        )

        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, product=zero_cost_product)

        initial_move_count = self.env["account.move"].search_count(
            [("journal_id", "=", self.compensation_journal.id)]
        )

        invoice.action_post()

        final_move_count = self.env["account.move"].search_count(
            [("journal_id", "=", self.compensation_journal.id)]
        )

        # No compensation move should be created for zero amount
        self.assertEqual(
            initial_move_count,
            final_move_count,
            "No compensation move should be created when amount is zero",
        )

    def test_07_multiple_lines_with_compensation(self):
        """Test compensation with multiple invoice lines using same CFOP.

        Validates:
        - Multiple lines with same CFOP are processed correctly
        - Total compensation equals sum of all eligible lines
        - Single compensation move consolidates all lines
        """
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_debit_account_type": "asset",
            }
        )

        # Create invoice with multiple lines
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.sales_journal.id,
                "invoice_date": "2025-01-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 5.0,
                            "price_unit": 150.00,
                            "account_id": self.account_revenue.id,
                            "cfop_id": self.cfop_5101.id,
                            "name": f"{self.product.name} - Line 1",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 3.0,
                            "price_unit": 150.00,
                            "account_id": self.account_revenue.id,
                            "cfop_id": self.cfop_5101.id,
                            "name": f"{self.product.name} - Line 2",
                        },
                    ),
                ],
            }
        )

        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        self.assertTrue(compensation_move, "Compensation move should be created")

        # Expected amount: (5 + 3) units * 100.00 cost = 800.00
        expected_amount = 800.00

        # Get total debit on off-balance asset account
        debit_lines = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset and l.debit > 0
        )
        total_debit = sum(debit_lines.mapped("debit"))

        # Should have compensation entries for both lines
        self.assertAlmostEqual(
            total_debit,
            expected_amount,
            places=2,
            msg="Total debit should sum compensation from all lines",
        )

    def test_08_mixed_cfop_lines(self):
        """Test invoice with mixed CFOP lines (with and without compensation).

        Validates:
        - Only lines with compensation-enabled CFOP are processed
        - Lines without compensation are correctly excluded
        - Mixed CFOP invoice posts successfully
        """
        # Configure only CFOP 5101 for compensation
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_debit_account_type": "asset",
            }
        )
        self.cfop_5102.use_compensation = False

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.sales_journal.id,
                "invoice_date": "2025-01-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 10.0,
                            "price_unit": 150.00,
                            "account_id": self.account_revenue.id,
                            "cfop_id": self.cfop_5101.id,  # With compensation
                            "name": f"{self.product.name} - CFOP 5101",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 5.0,
                            "price_unit": 150.00,
                            "account_id": self.account_revenue.id,
                            "cfop_id": self.cfop_5102.id,  # Without compensation
                            "name": f"{self.product.name} - CFOP 5102",
                        },
                    ),
                ],
            }
        )

        invoice.action_post()

        # Find compensation move
        compensation_move = self._get_compensation_move()

        self.assertTrue(
            compensation_move,
            "Compensation move should be created only for CFOP with compensation enabled",
        )

        # Expected amount: only 10 units from CFOP 5101 * 100.00 = 1000.00
        # CFOP 5102 line (5 units) should NOT be included
        expected_amount = 1000.00

        debit_lines = compensation_move.line_ids.filtered(
            lambda l: l.account_id == self.account_asset and l.debit > 0
        )
        total_debit = sum(debit_lines.mapped("debit"))

        self.assertAlmostEqual(
            total_debit,
            expected_amount,
            places=2,
            msg="Only lines with compensation-enabled CFOP should be included",
        )

    def test_09_compensation_journal_entry_structure(self):
        """Test the structure and balance of compensation journal entry.

        Validates:
        - Journal entry is properly balanced (debit = credit)
        - Correct number of move lines created
        - Reference field contains invoice information
        - Partner is correctly set on all lines
        """
        self.cfop_5101.write(
            {
                "use_compensation": True,
                "compensation_value_source": "cost",
                "compensation_debit_account_type": "asset",
            }
        )

        invoice = self._create_invoice(self.cfop_5101, quantity=10.0)
        invoice.action_post()

        compensation_move = self._get_compensation_move()

        # Verify journal entry is balanced
        total_debit = sum(compensation_move.line_ids.mapped("debit"))
        total_credit = sum(compensation_move.line_ids.mapped("credit"))

        self.assertAlmostEqual(
            total_debit,
            total_credit,
            places=2,
            msg="Journal entry must be balanced (debit = credit)",
        )

        # Verify entry has exactly 2 lines (1 debit + 1 credit)
        self.assertEqual(
            len(compensation_move.line_ids),
            2,
            "Compensation move should have exactly 2 lines for simple case",
        )

        # Verify reference contains invoice name
        self.assertIn(
            invoice.name,
            compensation_move.ref or "",
            "Compensation reference should mention source invoice",
        )

        # Verify partner is set
        for line in compensation_move.line_ids:
            self.assertEqual(
                line.partner_id,
                self.partner,
                "All lines should have the invoice partner",
            )
