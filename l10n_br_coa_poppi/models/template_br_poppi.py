# Copyright (C) 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models

from odoo.addons.account.models.chart_template import template

# Tax group (xmlid name part) -> (account code, refund account code)
# Data previously stored in l10n_br_coa.account.tax.group.account.template
# until v16, when the CoA template models were used.
POPPI_TAX_GROUP_ACCOUNTS = {
    "tax_group_pis": ("211.05.23", "112.07.06"),
    "tax_group_cofins": ("112.07.08", "112.07.08"),
    "tax_group_issqn": ("211.05.06", "211.05.06"),
    "tax_group_ipi": ("211.05.07", "112.07.02"),
}


# Values that must win over the ones set by the parent template (br_oca)
POPPI_TEMPLATE_DATA = {
    "code_digits": "9",
    "property_account_receivable_id": "account_template_poppi_112_01_01",
    "property_account_payable_id": "account_template_poppi_211_01_01",
    "property_account_expense_categ_id": "account_template_poppi_312_06_04",
    "property_account_income_categ_id": "account_template_poppi_411_01_01",
}
POPPI_COMPANY_DATA = {
    "cash_account_code_prefix": "111.01.",
    "bank_account_code_prefix": "111.02.",
    "transfer_account_code_prefix": "111.04.01",
    "anglo_saxon_accounting": True,
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_poppi")
    def _get_br_poppi_template_data(self):
        return {
            "name": _("Plano de Contas Poppi"),
            "parent": "br_oca",
            "visible": True,
            **POPPI_TEMPLATE_DATA,
        }

    @template("br_poppi", "res.company")
    def _get_br_poppi_res_company(self):
        return {self.env.company.id: dict(POPPI_COMPANY_DATA)}

    def _get_chart_template_data(self, template_code):
        data = super()._get_chart_template_data(template_code)
        if template_code == "br_poppi":
            # Odoo applies the parent template last, so its code_digits and
            # account code prefixes would override the Poppi ones.
            data["template_data"].update(POPPI_TEMPLATE_DATA)
            for company_values in data["res.company"].values():
                company_values.update(POPPI_COMPANY_DATA)
        return data

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(template_code, company, install_demo, force_create)
        if template_code == "br_poppi" and company.currency_id == self.env.ref(
            "base.BRL"
        ):
            self._set_poppi_tax_group_accounts(company)
        return result

    def _set_poppi_tax_group_accounts(self, company):
        """Set the Poppi accounts on the repartition lines of the PIS, COFINS,
        ISSQN and IPI taxes, replacing the generic accounts set by l10n_br_coa."""
        chart = self.with_company(company)
        env = chart.env
        Account = env["account.account"]
        for group_name, (code, refund_code) in POPPI_TAX_GROUP_ACCOUNTS.items():
            group = chart.ref(group_name)
            account = Account.search(
                [("code", "=", code), ("company_ids", "in", company.ids)], limit=1
            )
            refund_account = Account.search(
                [("code", "=", refund_code), ("company_ids", "in", company.ids)],
                limit=1,
            )
            if not (group and account and refund_account):
                continue
            taxes = env["account.tax"].search(
                [
                    ("company_id", "=", company.id),
                    ("tax_group_id", "=", group.id),
                ]
            )
            for tax in taxes:
                if tax.deductible or (
                    tax.withholdable and tax.type_tax_use != "purchase"
                ):
                    tax._update_repartition_lines(False, False)
                    # The parent helper only replaces a refund account when
                    # a truthy account ID is passed; clear it explicitly here.
                    tax.refund_repartition_line_ids.filtered(
                        lambda line: line.repartition_type == "tax"
                    ).account_id = False
                elif tax.type_tax_use == "purchase" and not tax.withholdable:
                    tax._update_repartition_lines(refund_account.id, account.id)
                else:
                    tax._update_repartition_lines(account.id, refund_account.id)
