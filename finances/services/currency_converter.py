import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class CurrencyConverter:  
    BASE_CURRENCY = 'USD'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_exchange_rates(cls):
        cache_key = 'openexchangerates_latest'
        rates = cache.get(cache_key)
        
        if rates is None:
            api_key = getattr(settings, 'OPENEXCHANGERATES_API_KEY', None)
            if not api_key:
                logger.warning("OPENEXCHANGERATES_API_KEY не налаштовано")
                return None
            
            try:
                url = f'https://openexchangerates.org/api/latest.json?app_id={api_key}&base={cls.BASE_CURRENCY}'
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                rates = data.get('rates', {})
                cache.set(cache_key, rates, cls.CACHE_TIMEOUT)
                logger.info("Курси валют отримано з API")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Помилка отримання курсів валют: {e}")
                return None
            except ValueError as e:
                logger.error(f"Помилка парсингу JSON: {e}")
                return None
        
        return rates
    
    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency='UAH'):
        """Конвертує суму з однієї валюти в іншу"""
        rates = cls.get_exchange_rates()
        if not rates:
            return None
        
        try:
            # Convert via USD
            if from_currency.upper() == cls.BASE_CURRENCY:
                amount_in_usd = float(amount)
            else:
                from_rate = rates.get(from_currency.upper())
                if not from_rate:
                    logger.error(f"Курс для валюти {from_currency} не знайдено")
                    return None
                amount_in_usd = float(amount) / from_rate
            
            if to_currency.upper() == cls.BASE_CURRENCY:
                return amount_in_usd
            
            to_rate = rates.get(to_currency.upper())
            if not to_rate:
                logger.error(f"Курс для валюти {to_currency} не знайдено")
                return None
            
            converted_amount = amount_in_usd * to_rate
            return round(converted_amount, 2)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Помилка конвертації: {e}")
            return None
    
    @classmethod
    def get_supported_currencies(cls):
        return {
            'UAH': 'Гривня',
            'USD': 'Долар США',
            'EUR': 'Євро',
        }