# Copyright 2025 - TODAY Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, fields, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _should_create_compensation(self):
        self.ensure_one()
        return (
            self.is_invoice(include_receipts=True)
            and self.state == "posted"
            and any(line.cfop_id.use_compensation for line in self.invoice_line_ids)
        )

    def _get_compensation_value(self, move_line):
        self.ensure_one()
        cfop = move_line.cfop_id
        product = move_line.product_id
        quantity = move_line.quantity

        if not cfop.compensation_value_source:
            return 0.0

        value_mapping = {
            "cost": product.standard_price,
            "sale_price": move_line.price_unit,
            "compensation_value": product.compensation_value,
        }

        value = value_mapping.get(cfop.compensation_value_source, 0.0)
        return value * quantity

    def _prepare_compensation_line_vals(self, line, amount, account, is_debit):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        line_desc = line.name or line.product_id.display_name or _("Line %s") % line.id

        return {
            "name": _("%s - %s (Compensation)")
            % (
                self.name,
                line_desc,
            ),
            "account_id": account.id,
            "debit": amount if is_debit else 0.0,
            "credit": 0.0 if is_debit else amount,
            "currency_id": currency.id,
            "amount_currency": amount if is_debit else -amount,
            "partner_id": self.partner_id.id,
            "exclude_from_invoice_tab": True,
        }

    def _prepare_compensation_move_vals(self, journal, line_vals):
        self.ensure_one()
        return {
            "name": "/",
            "date": self.date or fields.Date.context_today(self),
            "journal_id": journal.id,
            "company_id": self.company_id.id,
            "ref": _("Compensation for %s") % self.name,
            "move_type": "entry",
            "line_ids": line_vals,
        }

    def _create_compensation_entries(self):
        self.ensure_one()

        if not self._should_create_compensation():
            return self.env["account.move"]

        move_lines_vals = []
        journal = self.env["account.journal"]
        currency = self.currency_id or self.company_id.currency_id

        for line in self.invoice_line_ids.filtered(
            lambda l: l.cfop_id.use_compensation
        ):
            cfop = line.cfop_id
            journal = cfop.compensation_journal_id
            amount = self._get_compensation_value(line)
            if float_is_zero(amount, precision_rounding=currency.rounding):
                _logger.debug(
                    "Skipping compensation for line %s: amount is zero", line.id
                )
                continue

            accounts = cfop._get_compensation_debit_credit_accounts()
            debit_account = accounts["debit"]
            credit_account = accounts["credit"]

            if not debit_account or not credit_account:
                continue

            debit_vals = self._prepare_compensation_line_vals(
                line, amount, debit_account, is_debit=True
            )
            credit_vals = self._prepare_compensation_line_vals(
                line, amount, credit_account, is_debit=False
            )

            move_lines_vals.extend([(0, 0, debit_vals), (0, 0, credit_vals)])

        if not move_lines_vals or not journal:
            return self.env["account.move"]

        move_vals = self._prepare_compensation_move_vals(journal, move_lines_vals)
        compensation_move = self.env["account.move"].sudo().create(move_vals)
        compensation_move.action_post()

        return compensation_move

    def _post(self, soft=True):
        result = super()._post(soft=soft)
        posted_moves = self.filtered(lambda m: m._should_create_compensation())
        for move in posted_moves:
            move._create_compensation_entries()
        return result
