"""Map public Host headers to a database so /web/image works in emails.

With dbfilter=.* and multiple databases, anonymous requests have no DB selected
(logs show "INFO ?"), so mailing images return 404. This patch picks a DB from
the Host header when the session has none yet.
"""
import logging
import re

from odoo.http import Request, db_list

_logger = logging.getLogger(__name__)

# Hostname (no scheme/port) -> database name
HOST_DB_MAP = {
    'vitalimited.com': 'VPPL',
    'www.vitalimited.com': 'VPPL',
    # Direct server access (DNS for vitalimited.com currently points elsewhere)
    '194.164.150.184': 'VPPL',
}

_original_get_session_and_dbname = Request._get_session_and_dbname


def _normalize_host(host):
    host = (host or '').partition(':')[0].lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    return host


def _patched_get_session_and_dbname(self):
    session, dbname = _original_get_session_and_dbname(self)
    if dbname:
        return session, dbname

    host = _normalize_host(self.httprequest.environ.get('HTTP_HOST', ''))
    mapped = HOST_DB_MAP.get(host)
    if not mapped:
        return session, dbname

    try:
        available = db_list(force=True, host=self.httprequest.environ.get('HTTP_HOST', ''))
    except Exception:
        available = []

    if mapped in available:
        session.db = mapped
        _logger.debug('Host %s routed to database %s for anonymous request', host, mapped)
        return session, mapped

    return session, dbname


Request._get_session_and_dbname = _patched_get_session_and_dbname
