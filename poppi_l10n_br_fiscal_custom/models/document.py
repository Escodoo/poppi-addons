# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class Document(models.Model):

    _inherit = "l10n_br_fiscal.document"

    def action_send_email(self):
        """Open a window to compose an email, with the fiscal document_type
        template message loaded by default
        """
        self.ensure_one()
        template = self._get_email_template(self.state)
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        lang = self.env.context.get("lang")
        if template and template.lang:
            lang = template._render_template(template.lang, self._name, [self.id])
        self = self.with_context(lang=lang)
        ctx = dict(
            default_model="l10n_br_fiscal.document",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_attachment_ids=self._get_mail_attachment(),
            default_template_id=template and template.id or False,
            default_composition_mode="mass_mail",
            model_description=self.document_type_id.name or self._name,
            force_email=True,
        )
        return {
            "name": _("Send Fiscal Document Email Notification"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
