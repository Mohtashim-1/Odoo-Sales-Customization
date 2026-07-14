import json
import logging
import urllib.error
import urllib.request

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CURRENCY_API_URL = 'https://open.er-api.com/v6/latest/{base}'

# Currencies commonly used on MTJ export orders — activated automatically before rate fetch.
MTJ_ORDER_CURRENCIES = (
    'USD', 'PKR', 'EUR', 'INR', 'GBP', 'AED', 'CNY', 'SAR', 'CAD', 'AUD', 'CHF', 'JPY',
)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _mtj_fetch_rates_from_api(self, base_currency_code):
        """Fetch exchange rates from open.er-api.com (free, no API key)."""
        url = CURRENCY_API_URL.format(base=base_currency_code)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.URLError as error:
            raise UserError(_('Could not reach currency rate API: %s') % error) from error

        if payload.get('result') != 'success':
            raise UserError(
                _('Currency API error: %s') % payload.get('error-type', 'unknown')
            )
        return payload.get('rates', {})

    @api.model
    def _mtj_activate_order_currencies(self):
        """Ensure common order currencies are active so they appear on sale orders."""
        currencies = self.with_context(active_test=False).search([
            ('name', 'in', MTJ_ORDER_CURRENCIES),
            ('active', '=', False),
        ])
        if currencies:
            currencies.write({'active': True})
            _logger.info('Activated currencies for MTJ orders: %s', ', '.join(currencies.mapped('name')))
        return len(currencies)

    @api.model
    def _mtj_update_company_rates(self, company, rate_date=None):
        """Update today's rates for all active currencies of a company."""
        self._mtj_activate_order_currencies()
        company = company or self.env.company
        rate_date = rate_date or fields.Date.context_today(self)
        base_currency = company.currency_id
        if not base_currency:
            return 0

        target_currencies = self.search([
            ('active', '=', True),
            ('id', '!=', base_currency.id),
        ])
        if not target_currencies:
            return 0

        api_rates = self._mtj_fetch_rates_from_api(base_currency.name)
        Rate = self.env['res.currency.rate'].sudo()
        last_rates = Rate._get_last_rates_for_companies(company)
        base_last_rate = last_rates.get(company) or 1.0
        updated = 0

        for currency in target_currencies:
            api_rate = api_rates.get(currency.name)
            if not api_rate or api_rate <= 0:
                _logger.info(
                    'No API rate for %s (company %s, base %s)',
                    currency.name,
                    company.name,
                    base_currency.name,
                )
                continue

            # API returns "foreign per 1 company currency". Odoo's technical rate
            # is relative to the rate-1 currency, so scale by the base currency rate.
            technical_rate = api_rate * base_last_rate

            existing = Rate.search([
                ('currency_id', '=', currency.id),
                ('company_id', '=', company.id),
                ('name', '=', rate_date),
            ], limit=1)
            vals = {'rate': technical_rate}
            if existing:
                existing.write(vals)
            else:
                Rate.create({
                    'name': rate_date,
                    'currency_id': currency.id,
                    'company_id': company.id,
                    **vals,
                })
            updated += 1

        _logger.info(
            'Currency rates updated for %s: %s currencies (base %s, date %s)',
            company.name,
            updated,
            base_currency.name,
            rate_date,
        )
        return updated

    @api.model
    def cron_fetch_daily_exchange_rates(self):
        """Scheduled job: fetch rates for every company from the free API."""
        total = 0
        for company in self.env['res.company'].sudo().search([]):
            try:
                total += self._mtj_update_company_rates(company)
            except UserError as error:
                _logger.warning(
                    'Currency rate fetch skipped for %s: %s',
                    company.name,
                    error,
                )
            except Exception:
                _logger.exception('Currency rate fetch failed for %s', company.name)
        return total

    def action_fetch_exchange_rates_now(self):
        """Manual refresh from active currencies list view / settings."""
        total = self.cron_fetch_daily_exchange_rates()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Currency Rates'),
                'message': _('Updated %s currency rate(s) from the live API.') % total,
                'type': 'success',
                'sticky': False,
            },
        }
