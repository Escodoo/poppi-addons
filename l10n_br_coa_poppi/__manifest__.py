# Copyright 2023 - TODAY, Escodoo
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Plano de Contas Poppi",
    "summary": "Plano de Contas Formato Poppi",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Escodoo",
    "development_status": "Production/Stable",
    "website": "https://github.com/Escodoo/poppi-addons",
    "version": "14.0.1.0.0",
    "depends": ["l10n_br_coa"],
    "data": [
        "data/l10n_br_coa_poppi_template.xml",
        "data/account_group.xml",
        "data/account.account.template.csv",
        "data/l10n_br_coa.account.tax.group.account.template.csv",
        "data/l10n_br_coa_poppi_template_post.xml",
    ],
    "demo": [
        "demo/res_company.xml",
        "demo/res_user.xml",
    ],
    "post_init_hook": "post_init_hook",
}
