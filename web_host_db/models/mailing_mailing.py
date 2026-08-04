import re

from odoo import api, models

# Path must stop at ?/# so the query string is not swallowed into the path
# (otherwise we append a second ?access_token=... and mail clients get a placeholder).
IMG_SRC_RE = re.compile(
    r"""(<img\b[^>]*\bsrc=["'])(/web/image/(\d+)(?:-[^/"'?#\s]*)?(?:/[^"'?#]*)?)([^"']*)(["'])""",
    re.IGNORECASE,
)


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    def _ensure_mailing_image_access(self):
        """Ensure every /web/image/<id> in the body has a valid access_token and is public."""
        Attachment = self.env['ir.attachment'].sudo()
        for mailing in self:
            body = mailing.body_html or ''
            if '/web/image/' not in body:
                continue

            def _replace(match):
                prefix, path, att_id, query, suffix = match.groups()
                attachment = Attachment.browse(int(att_id))
                if not attachment.exists():
                    return match.group(0)
                if not attachment.access_token:
                    attachment.generate_access_token()
                if not attachment.public:
                    attachment.public = True
                # Drop every access_token (including malformed ?token=?token) then set one.
                query = re.sub(r'[?&]access_token=[^&?]*', '', query or '')
                query = query.replace('?&', '?').replace('&&', '&').rstrip('?&')
                if query and not query.startswith('?'):
                    query = '?' + query
                if query:
                    new_query = f'{query}&access_token={attachment.access_token}'
                else:
                    new_query = f'?access_token={attachment.access_token}'
                return f'{prefix}{path}{new_query}{suffix}'

            new_body = IMG_SRC_RE.sub(_replace, body)
            if new_body != body:
                super(MailingMailing, mailing).write({'body_html': new_body})

            # Also publish mailing-linked attachments used by this campaign.
            attachments = Attachment.search([
                ('res_model', '=', 'mailing.mailing'),
                ('res_id', 'in', [mailing.id, 0]),
                ('mimetype', 'ilike', 'image%'),
            ])
            to_fix = attachments.filtered(lambda a: not a.public)
            if to_fix:
                to_fix.write({'public': True})
            for attachment in attachments.filtered(lambda a: not a.access_token):
                attachment.generate_access_token()

    @api.model_create_multi
    def create(self, vals_list):
        mailings = super().create(vals_list)
        mailings._ensure_mailing_image_access()
        return mailings

    def write(self, vals):
        res = super().write(vals)
        if 'body_html' in vals or 'body_arch' in vals:
            self._ensure_mailing_image_access()
        return res

    def action_send_mail(self, res_ids=None):
        self._ensure_mailing_image_access()
        return super().action_send_mail(res_ids=res_ids)

    def _create_attachments_from_inline_images(self, b64images):
        urls = super()._create_attachments_from_inline_images(b64images)
        # Publish newly created mailing images so email clients can fetch them.
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'mailing.mailing'),
            ('res_id', '=', self.id),
            ('mimetype', 'ilike', 'image%'),
        ])
        if attachments:
            attachments.filtered(lambda a: not a.public).write({'public': True})
        return urls
