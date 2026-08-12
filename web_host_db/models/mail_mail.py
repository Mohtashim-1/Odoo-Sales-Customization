import base64
import logging
import re
import urllib.request

from odoo import models

_logger = logging.getLogger(__name__)

IMG_SRC_RE = re.compile(
    r'(<img\b[^>]*?)(?<![\w-])src=(["\'])([^"\']+)\2',
    re.IGNORECASE,
)
WEB_IMAGE_ID_RE = re.compile(r'/web/image/(\d+)')


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _embed_mailing_images(self, body):
        """Embed Odoo-hosted images so HTTPS webmail clients can display them.

        Gmail proxies remote images over HTTPS, but many webmail clients (Roundcube,
        cPanel, Outlook Web) block mixed content when the page is HTTPS and image
        URLs are plain HTTP (e.g. http://194.164.150.184:1821/web/image/...).
        """
        if not body or '<img' not in body:
            return body

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')
        Attachment = self.env['ir.attachment'].sudo()
        cache = {}

        def _to_data_url(src):
            if src in cache:
                return cache[src]
            if src.startswith('data:'):
                cache[src] = src
                return src

            abs_url = src
            if src.startswith('/'):
                abs_url = f'{base_url}{src}'
            elif not src.startswith('http'):
                cache[src] = src
                return src

            is_odoo_image = '/web/image/' in abs_url or '/web_editor/' in abs_url
            is_our_host = base_url and abs_url.startswith(base_url)
            if not is_odoo_image and not is_our_host:
                cache[src] = src
                return src

            mimetype = 'image/png'
            b64data = None
            match = WEB_IMAGE_ID_RE.search(src)
            if match:
                attachment = Attachment.browse(int(match.group(1)))
                if attachment.exists():
                    attachment = attachment.with_context(bin_size=False)
                    if attachment.datas:
                        mimetype = attachment.mimetype or mimetype
                        b64data = attachment.datas
                        if isinstance(b64data, bytes):
                            b64data = b64data.decode()

            if not b64data:
                try:
                    with urllib.request.urlopen(abs_url, timeout=15) as response:
                        raw = response.read()
                        mimetype = (response.headers.get('Content-Type') or mimetype).split(';')[0]
                        b64data = base64.b64encode(raw).decode()
                except Exception as error:
                    _logger.warning('Could not embed mailing image %s: %s', abs_url, error)
                    cache[src] = src
                    return src

            data_url = f'data:{mimetype};base64,{b64data}'
            cache[src] = data_url
            return data_url

        def _replace(match):
            prefix, quote, src = match.groups()
            return f'{prefix}src={quote}{_to_data_url(src)}{quote}'

        return IMG_SRC_RE.sub(_replace, body)

    def _prepare_outgoing_body(self):
        body = super()._prepare_outgoing_body()
        if self.mailing_id and body:
            body = self._embed_mailing_images(body)
        return body
