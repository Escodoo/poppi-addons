# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Cfop(models.Model):

    _inherit = "l10n_br_fiscal.cfop"

    use_compensation = fields.Boolean()
    compensation_value_source = fields.Selection(
        selection=[
            ("cost", "Cost"),
            ("sale_price", "Sale Price"),
            ("compensation_value", "Compensation Value"),
        ],
        string="Value Source",
    )
    compensation_account_asset = fields.Many2one(
        comodel_name="account.account",
        string="Debit Account",
    )
    compensation_account_liability = fields.Many2one(
        comodel_name="account.account",
        string="Credit Account",
    )
    compensation_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=[
            ("type", "=", "general"),
        ],
    )
    compensation_debit_account_type = fields.Selection(
        selection=[
            ("asset", "Asset Account"),
            ("liability", "Liability Account"),
        ],
        string="Debit Account Type",
        default="asset",
    )

    def _get_compensation_debit_credit_accounts(self):
        """Get debit and credit accounts for compensation based on CFOP configuration.

        Determines the correct debit and credit accounts for compensation entries
        based on the CFOP's selected debit account type and whether it's an
        outgoing (remessa) or return (retorno) movement.

        :return: Dictionary with 'debit' and 'credit' account.account records.
        """
        self.ensure_one()

        asset_account = self.compensation_account_asset
        liability_account = self.compensation_account_liability
        debit_type = self.compensation_debit_account_type

        if debit_type == "asset":
            debit_account = asset_account
            credit_account = liability_account
        else:
            debit_account = liability_account
            credit_account = asset_account

        return {"debit": debit_account, "credit": credit_account}
