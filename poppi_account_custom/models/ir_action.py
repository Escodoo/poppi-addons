# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        try:
            return super()._post_pdf(save_in_attachment, pdf_content, res_ids)
        except AssertionError:
            return pdf_content
