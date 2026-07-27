# -*- coding: utf-8 -*-
import re

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _prepare_html(self, html, report_model=False):
        bodies, res_ids, header, footer, specific_paperformat_args = super()._prepare_html(
            html, report_model=report_model
        )
        # Odoo calls _prepare_html on an empty recordset, so detect via header markup.
        # minimal_layout (body.container + report CSS + html{height:0}) makes wkhtmltopdf
        # leave a large blank band above the letterhead — strip that chrome.
        header_str = header if isinstance(header, str) else (header.decode() if header else "")
        if "company-letterhead" in header_str or "company-letterhead" in (html if isinstance(html, str) else ""):
            header = self._minimal_wkhtmltopdf_chrome(header)
            footer = self._minimal_wkhtmltopdf_chrome(footer)
        return bodies, res_ids, header, footer, specific_paperformat_args

    def _minimal_wkhtmltopdf_chrome(self, html_doc):
        """Rebuild header/footer HTML without Odoo minimal_layout chrome."""
        if not html_doc:
            return html_doc
        raw = html_doc if isinstance(html_doc, str) else html_doc.decode()
        match = re.search(
            r'<div id="minimal_layout_report_(?:headers|footers)">(.*)</div>\s*</body>',
            raw,
            flags=re.DOTALL | re.IGNORECASE,
        )
        inner = match.group(1).strip() if match else ""
        if not inner:
            match = re.search(r"<body[^>]*>(.*)</body>", raw, flags=re.DOTALL | re.IGNORECASE)
            inner = match.group(1).strip() if match else raw
        return (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head><meta charset=\"utf-8\"/></head>\n"
            "<body style=\"margin:0;padding:0;\">\n"
            f"{inner}\n"
            "</body>\n"
            "</html>"
        )
