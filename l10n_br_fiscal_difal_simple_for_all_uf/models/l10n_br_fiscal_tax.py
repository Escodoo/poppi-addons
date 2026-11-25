# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from ..constants.icms import ICMS_DIFAL_UNIQUE_BASE


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    @api.model
    def _compute_icms(self, tax, taxes_dict, **kwargs):
        result = super()._compute_icms(tax, taxes_dict, **kwargs)
        icms = result[tax.tax_domain]
        # The fiscal engine sets the sharing percentage only when DIFAL applies.
        if (
            "icms_sharing_percent" not in icms
            or kwargs["partner"].state_id.code not in ICMS_DIFAL_UNIQUE_BASE
        ):
            return result

        currency = kwargs.get("currency") or kwargs["company"].currency_id
        base = icms["base"]
        destination_icms = currency.round(base * icms["icms_dest_perc"] / 100)
        difal = destination_icms - icms["tax_value"]
        icms.update(
            icms_dest_base=base,
            icms_origin_value=currency.round(difal * icms["difal_origin_perc"] / 100),
            icms_dest_value=currency.round(difal * icms["difal_dest_perc"] / 100),
        )
        return result
