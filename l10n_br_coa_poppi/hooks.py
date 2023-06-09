# Copyright (C) 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_tmpl = env.ref("l10n_br_coa_poppi.l10n_br_coa_poppi_chart_template")
    if env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_account"),
            ("state", "=", "installed"),
        ]
    ):
        from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes

        # Relate fiscal taxes to account taxes.
        load_fiscal_taxes(env, coa_tmpl)

    # Load COA to Demo Company
    if not tools.config.get("without_demo"):
        company = env.ref("l10n_br_coa_poppi.poppi_company", raise_if_not_found=False)
        if company:
            coa_tmpl.try_loading(company=company)
            tools.convert_file(
                cr,
                "l10n_br_coa_poppi",
                "demo/account_journal.xml",
                None,
                mode="init",
                noupdate=True,
                kind="init",
            )
