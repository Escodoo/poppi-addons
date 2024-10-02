# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    FINAL_CUSTOMER_NO,
    FISCAL_IN,
    FISCAL_OUT,
    NFE_IND_IE_DEST_9,
)
from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_DIFAL_PARTITION

from ..constants.icms import ICMS_DIFAL_DOUBLE_BASE, ICMS_DIFAL_UNIQUE_BASE


class Tax(models.Model):

    _inherit = "l10n_br_fiscal.tax"

    @api.model
    def _compute_icms(self, tax, taxes_dict, **kwargs):
        result = super()._compute_icms(tax, taxes_dict, **kwargs)
        tax_dict = taxes_dict.get(tax.tax_domain)
        partner = kwargs.get("partner")
        company = kwargs.get("company")
        product = kwargs.get("product")
        currency = kwargs.get("currency", company.currency_id)
        ncm = kwargs.get("ncm")
        nbm = kwargs.get("nbm")
        cest = kwargs.get("cest")
        operation_line = kwargs.get("operation_line")
        cfop = kwargs.get("cfop")
        ind_final = kwargs.get("ind_final", FINAL_CUSTOMER_NO)
        kwargs.get("icms_cst_id", self.env["l10n_br_fiscal.cst"])

        # Get Computed IPI Tax
        taxes_dict.get("ipi", {})

        if (
            cfop
            and cfop.destination == CFOP_DESTINATION_EXTERNAL
            and partner.ind_ie_dest == NFE_IND_IE_DEST_9
            and tax_dict.get("tax_value")
            and operation_line.fiscal_operation_type == FISCAL_OUT
            or operation_line.fiscal_operation_id.fiscal_type == "return_in"
            and operation_line.fiscal_operation_type == FISCAL_IN
        ):
            icms_tax_difal, _ = company.icms_regulation_id.map_tax_def_icms_difal(
                company, partner, product, ncm, nbm, cest, operation_line, ind_final
            )
            icmsfcp_tax_difal = taxes_dict.get("icmsfcp", {})

            # Difal - Origin Percent
            icms_origin_perc = tax_dict.get("percent_amount")

            # Difal - Origin Value
            icms_origin_value = tax_dict.get("tax_value")

            # Difal - Destination Percent
            icms_dest_perc = 0.00
            if icms_tax_difal:
                icms_dest_perc = icms_tax_difal[0].percent_amount

            # Difal - FCP Percent
            icmsfcp_perc = 0.00
            if icmsfcp_tax_difal:
                icmsfcp_perc = icmsfcp_tax_difal.get("percent_amount")

            # Difal - Base
            icms_base = tax_dict.get("base")
            difal_icms_base = 0.00

            # Difal - ICMS Dest Value
            icms_dest_value = currency.round(icms_base * (icms_dest_perc / 100))

            if partner.state_id.code in ICMS_DIFAL_UNIQUE_BASE:
                difal_icms_base = icms_base

            if partner.state_id.code in ICMS_DIFAL_DOUBLE_BASE:
                difal_icms_base = currency.round(
                    (icms_base - icms_origin_value)
                    / (1 - ((icms_dest_perc + icmsfcp_perc) / 100))
                )

                icms_dest_value = currency.round(
                    difal_icms_base * (icms_dest_perc / 100)
                )

            difal_value = icms_dest_value - icms_origin_value

            # Difal - Sharing Percent
            date_year = fields.Date.today().year

            if date_year >= 2019:
                tax_dict.update(ICMS_DIFAL_PARTITION[2019])
            else:
                if date_year == 2018:
                    tax_dict.update(ICMS_DIFAL_PARTITION[2018])
                if date_year == 2017:
                    tax_dict.update(ICMS_DIFAL_PARTITION[2017])
                else:
                    tax_dict.update(ICMS_DIFAL_PARTITION[2016])

            difal_share_origin = tax_dict.get("difal_origin_perc")

            difal_share_dest = tax_dict.get("difal_dest_perc")

            difal_origin_value = currency.round(difal_value * difal_share_origin / 100)
            difal_dest_value = currency.round(difal_value * difal_share_dest / 100)

            tax_dict.update(
                {
                    "icms_origin_perc": icms_origin_perc,
                    "icms_dest_perc": icms_dest_perc,
                    "icms_dest_base": difal_icms_base,
                    "icms_sharing_percent": difal_share_dest,
                    "icms_origin_value": difal_origin_value,
                    "icms_dest_value": difal_dest_value,
                }
            )

            result[tax.tax_domain] = tax_dict

        return result
