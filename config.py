"""
Configuration management for Amazon Affiliate Deal Bot.
Handles environment variables, regional settings, and affiliate link generation.
"""

import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the deal bot."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Core API configurations
        self.BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN', ''))
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'mongodb+srv://primebaby11220:TuGa0I5ZsiC8mp5A@cluster0.df4rivj.mongodb.net/?retryWrites=true&w=majority')
        self.FLASK_PORT = int(os.environ.get("PORT", 5000))
        # Amazon affiliate configuration
        self.AFFILIATE_ID = os.getenv('AMAZON_AFFILIATE_ID', os.getenv('AFFILIATE_ID', 'ironman1122-21'))
        
        # Telegram configuration
        self.TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', os.getenv('TELEGRAM_CHENNAL', '@Amazon_Flipkartt_Offers'))
        
        # Scraping configuration
        self.MAX_DEALS_PER_SOURCE = int(os.getenv('MAX_DEALS_PER_SOURCE', '5'))
        self.POST_INTERVAL_MINUTES = int(os.getenv('POST_INTERVAL_MINUTES', '6'))
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', '2'))
        
        # Web dashboard configuration
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
        self.FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Regional affiliate IDs for different Amazon markets
        self.REGIONAL_AFFILIATE_IDS = {
            'US': self.AFFILIATE_ID,  # amazon.com
            'UK': os.getenv('AFFILIATE_ID_UK', self.AFFILIATE_ID),  # amazon.co.uk
            'DE': os.getenv('AFFILIATE_ID_DE', self.AFFILIATE_ID),  # amazon.de
            'FR': os.getenv('AFFILIATE_ID_FR', self.AFFILIATE_ID),  # amazon.fr
            'CA': os.getenv('AFFILIATE_ID_CA', self.AFFILIATE_ID),  # amazon.ca
            'JP': os.getenv('AFFILIATE_ID_JP', self.AFFILIATE_ID),  # amazon.co.jp
            'AU': os.getenv('AFFILIATE_ID_AU', self.AFFILIATE_ID),  # amazon.com.au
            'IN': os.getenv('AFFILIATE_ID_IN', self.AFFILIATE_ID),  # amazon.in
        }
        
        # Regional currency and formatting
        self.REGIONAL_CURRENCIES = {
            'US': {'symbol': '$', 'code': 'USD', 'domain': 'amazon.com'},
            'UK': {'symbol': '£', 'code': 'GBP', 'domain': 'amazon.co.uk'},
            'DE': {'symbol': '€', 'code': 'EUR', 'domain': 'amazon.de'},
            'FR': {'symbol': '€', 'code': 'EUR', 'domain': 'amazon.fr'},
            'CA': {'symbol': 'C$', 'code': 'CAD', 'domain': 'amazon.ca'},
            'JP': {'symbol': '¥', 'code': 'JPY', 'domain': 'amazon.co.jp'},
            'AU': {'symbol': 'A$', 'code': 'AUD', 'domain': 'amazon.com.au'},
            'IN': {'symbol': '₹', 'code': 'INR', 'domain': 'amazon.in'},
        }
        
        # Default region
        self.DEFAULT_REGION = os.getenv('DEFAULT_REGION', 'IN')
        
        # Admin user configuration
        admin_ids_str = os.getenv('ADMIN_USER_IDS', '949657126')
        self.ADMIN_USER_IDS = [int(uid.strip()) for uid in admin_ids_str.split(',') if uid.strip().isdigit()] if admin_ids_str else []
        
        # Log configuration status
        self._log_configuration()
    
    def _log_configuration(self):
        """Log configuration status."""
        logger.info("📋 Configuration loaded:")
        logger.info(f"  🤖 Bot configured: {self.bot_configured}")
        logger.info(f"  🧠 OpenAI configured: {self.openai_configured}")
        logger.info(f"  📊 Database configured: {self.database_configured}")
        logger.info(f"  🛒 Affiliate ID: {self.AFFILIATE_ID}")
        logger.info(f"  📢 Telegram channel: {self.TELEGRAM_CHANNEL or 'Not configured'}")
        logger.info(f"  🌍 Default region: {self.DEFAULT_REGION}")
    
    @property
    def bot_configured(self) -> bool:
        """Check if Telegram bot is configured."""
        return bool(self.BOT_TOKEN)
    
    @property
    def openai_configured(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.OPENAI_API_KEY)
    
    @property
    def database_configured(self) -> bool:
        """Check if database is configured."""
        return bool(self.DATABASE_URL and self.DATABASE_URL.startswith('postgresql'))
    
    @property
    def POST_INTERVAL_HOURS(self) -> float:
        """Get posting interval in hours."""
        return self.POST_INTERVAL_MINUTES / 60.0
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.bot_configured:
            logger.warning("⚠️ BOT_TOKEN not configured - bot functionality disabled")
        
        if not self.openai_configured:
            logger.warning("⚠️ OPENAI_API_KEY not configured - using fallback content generation")
        
        if not self.database_configured:
            logger.warning("⚠️ DATABASE_URL not configured - using in-memory database")
        
        # At minimum we need some functionality
        return True  # Allow running with limited functionality
    
    def get_affiliate_link(self, product_url: str, region: Optional[str] = None) -> str:
        """Generate affiliate link for a product URL with regional support."""
        if not product_url:
            return ""
        
        region = region or self.DEFAULT_REGION
        affiliate_id = self.REGIONAL_AFFILIATE_IDS.get(region, self.AFFILIATE_ID)
        
        try:
            # Extract ASIN from URL
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
            if not asin_match:
                asin_match = re.search(r'/gp/product/([A-Z0-9]{10})', product_url)
            
            if asin_match:
                asin = asin_match.group(1)
                
                # Preserve original domain from URL
                if 'amazon.co.uk' in product_url:
                    domain = 'amazon.co.uk'
                elif 'amazon.de' in product_url:
                    domain = 'amazon.de'
                elif 'amazon.fr' in product_url:
                    domain = 'amazon.fr'
                elif 'amazon.ca' in product_url:
                    domain = 'amazon.ca'
                elif 'amazon.com.au' in product_url:
                    domain = 'amazon.com.au'
                elif 'amazon.co.jp' in product_url:
                    domain = 'amazon.co.jp'
                elif 'amazon.com' in product_url:
                    domain = 'amazon.com'
                else:
                    domain = 'www.amazon.in'  # Default to www.amazon.com for US
                
                return f"https://{domain}/dp/{asin}?tag={affiliate_id}&linkCode=as2&camp=1789&creative=9325"
            
            # Fallback: add tag parameter to existing URL
            separator = '&' if '?' in product_url else '?'
            return f"{product_url}{separator}tag={affiliate_id}&linkCode=as2&camp=1789&creative=9325"
            
        except Exception as e:
            logger.error(f"Error generating affiliate link: {e}")
            separator = '&' if '?' in product_url else '?'
            return f"{product_url}{separator}tag={affiliate_id}"
    
    def get_regional_currency(self, region: Optional[str] = None) -> Dict[str, str]:
        """Get currency information for a region."""
        region = region or self.DEFAULT_REGION
        return self.REGIONAL_CURRENCIES.get(region, self.REGIONAL_CURRENCIES['US'])
    
    def format_price_for_region(self, price: str, region: Optional[str] = None) -> str:
        """Format price for a specific region."""
        region = region or self.DEFAULT_REGION
        currency_info = self.get_regional_currency(region)
        
        try:
            # Extract numeric value
            numeric_price = re.sub(r'[^\d.,]', '', price)
            
            # Handle different decimal separators
            if ',' in numeric_price and '.' in numeric_price:
                # Both comma and period - assume comma is thousands separator
                numeric_price = numeric_price.replace(',', '')
            elif ',' in numeric_price and region in ['DE', 'FR']:
                # European format - comma as decimal separator
                numeric_price = numeric_price.replace(',', '.')
            
            price_value = float(numeric_price)
            
            # Format based on region
            if region == 'JP':
                # No decimal places for Japanese Yen
                return f"{currency_info['symbol']}{int(price_value):,}"
            else:
                return f"{currency_info['symbol']}{price_value:,.2f}"
                
        except (ValueError, TypeError):
            # Fallback to original price with regional symbol
            return f"{currency_info['symbol']}{price}"
    
    def get_supported_regions(self) -> list:
        """Get list of supported regions."""
        return list(self.REGIONAL_CURRENCIES.keys())
    
    def get_region_info(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive region information."""
        effective_region: str = region or self.DEFAULT_REGION
        
        if effective_region not in self.REGIONAL_CURRENCIES:
            effective_region = self.DEFAULT_REGION
        
        currency_info = self.REGIONAL_CURRENCIES[effective_region]
        
        return {
            'region': effective_region,
            'currency_symbol': currency_info['symbol'],
            'currency_code': currency_info['code'],
            'amazon_domain': currency_info['domain'],
            'affiliate_id': self.REGIONAL_AFFILIATE_IDS.get(effective_region, self.AFFILIATE_ID)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for debugging)."""
        return {
            'bot_configured': self.bot_configured,
            'openai_configured': self.openai_configured,
            'database_configured': self.database_configured,
            'affiliate_id': self.AFFILIATE_ID,
            'telegram_channel': self.TELEGRAM_CHANNEL,
            'default_region': self.DEFAULT_REGION,
            'max_deals_per_source': self.MAX_DEALS_PER_SOURCE,
            'post_interval_minutes': self.POST_INTERVAL_MINUTES,
            'supported_regions': self.get_supported_regions()
        }
