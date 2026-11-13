# Copyright (C) 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import tools


def post_init_hook(env):
    # Load COA for demo Company
    company_poppi = env.ref("l10n_br_coa_poppi.poppi_company", raise_if_not_found=False)
    if company_poppi:
        env["account.chart.template"].try_loading(
            "br_poppi", company_poppi, install_demo=True
        )
        tools.convert_file(
            env,
            "l10n_br_coa_poppi",
            "demo/account_journal.xml",
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
