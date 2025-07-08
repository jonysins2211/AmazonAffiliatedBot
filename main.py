#!/usr/bin/env python3
"""
Amazon Affiliate Deal Bot - Main Application
Production-ready Telegram bot with web dashboard for Amazon affiliate deals.
"""

import asyncio
import logging
import os
import signal
import sys
import threading
from datetime import datetime
from typing import Optional
from aiogram import types

import dotenv

# Load environment variables
dotenv.load_dotenv()


from config import Config
from telegram_bot import AffiliateBot
from web_dashboard_clean import create_app
from scheduler import TaskScheduler
from database import DatabaseManager
from database_simple import SimpleDatabaseManager
from content_generator import ContentGenerator
from scraper import DealScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dealbot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class DealBotApplication:
    """Main application class for the Amazon Affiliate Deal Bot."""
    
    def __init__(self):
        """Initialize the application."""
        self.config = Config()
        self.running = False
        self.bot: Optional[AffiliateBot] = None
        self.db_manager = None  # Can be DatabaseManager or SimpleDatabaseManager
        self.scheduler: Optional[TaskScheduler] = None
        self.web_app = None
        self.web_thread: Optional[threading.Thread] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def initialize(self) -> bool:
        """Initialize all application components."""
        try:
            logger.info("🚀 Initializing Amazon Affiliate Deal Bot...")
            
            # Validate configuration
            if not self.config.validate():
                logger.error("❌ Configuration validation failed")
                return False
            
            # Initialize database manager (prevent multiple initializations)
            if not self.db_manager:
                try:
                    if self.config.database_configured:
                        self.db_manager = DatabaseManager(self.config.DATABASE_URL)
                        logger.info("📊 Using PostgreSQL database")
                        await self.db_manager.initialize()
                    else:
                        self.db_manager = SimpleDatabaseManager()
                        logger.info("📊 Using in-memory database")
                        await self.db_manager.initialize()
                except Exception as e:
                    logger.warning(f"Database initialization failed: {e}, falling back to in-memory database")
                    self.db_manager = SimpleDatabaseManager()
                    await self.db_manager.initialize()
            else:
                logger.info("📊 Database manager already initialized")
            
            # Initialize Telegram bot
            if self.config.bot_configured:
                self.bot = AffiliateBot(self.config)
                await self.bot.initialize()
                logger.info("🤖 Telegram bot initialized")
            else:
                logger.warning("⚠️ Telegram bot not configured (missing BOT_TOKEN)")
            
            # Initialize task scheduler
            if self.bot:
                self.scheduler = TaskScheduler(self.bot, self.config)
                logger.info("⏰ Task scheduler initialized")
            
            # Initialize web dashboard
            self.web_app = create_app(self.config)
            logger.info("🌐 Web dashboard initialized")
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start_bot_only(self):
        """Start only the Telegram bot (no web dashboard)."""
        if not self.bot:
            logger.error("❌ Bot not initialized")
            return
        
        try:
            logger.info("🤖 Starting Telegram bot only...")
            await self.bot.start_polling()
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
    
    async def start_web_only(self):
        """Start only the web dashboard (no Telegram bot)."""
        try:
            logger.info("🌐 Starting web dashboard only...")
            if self.web_app:
                self.web_app.run(
                    host=self.config.FLASK_HOST,
                    port=self.config.FLASK_PORT,
                    debug=False
                )
            else:
                logger.error("❌ Web app not initialized")
        except Exception as e:
            logger.error(f"❌ Web dashboard error: {e}")
    
    async def start_hybrid_mode(self):
        """Start both bot and web dashboard."""
        if not self.bot:
            logger.error("❌ Cannot start hybrid mode without bot")
            return
        
        try:
            logger.info("🚀 Starting hybrid mode (bot + web dashboard)...")
            
            # Start web dashboard in a separate thread with proper initialization
            import threading
            import time
            
            def run_web():
                try:
                    # Give a moment for the main thread to set up
                    time.sleep(1)
                    logger.info(f"🌐 Web dashboard thread starting on {self.config.FLASK_HOST}:{self.config.FLASK_PORT}")
                    if self.web_app:
                        self.web_app.run(
                            host=self.config.FLASK_HOST,
                            port=self.config.FLASK_PORT,
                            debug=False,
                            use_reloader=False,
                            threaded=True
                        )
                except Exception as e:
                    logger.error(f"Web dashboard thread error: {e}")
            
            self.web_thread = threading.Thread(target=run_web, daemon=True)
            self.web_thread.start()
            
            # Wait a moment for web server to start
            await asyncio.sleep(2)
            logger.info(f"🌐 Web dashboard should be running on http://{self.config.FLASK_HOST}:{self.config.FLASK_PORT}")
            
            # Start task scheduler
            if self.scheduler:
                scheduler_task = asyncio.create_task(self.scheduler.start())
                logger.info("⏰ Task scheduler started")
            
            # Start bot polling
            logger.info("🤖 Starting bot polling...")
            await self.bot.start_polling()
            
        except Exception as e:
            logger.error(f"❌ Hybrid mode error: {e}")
    

    
    async def post_deals(self) -> int:
        """Post new deals to Telegram channel with link validation."""
        if not self.bot:
            logger.warning("⚠️ No bot available for posting deals")
            return 0
        
        try:
            from link_validator import LinkValidator
            
            # Get new deals from scraper
            scraper = DealScraper(
                max_deals_per_source=self.config.MAX_DEALS_PER_SOURCE
            )
            await scraper.initialize()
            
            deals = await scraper.scrape_real_amazon_deals()
            await scraper.close()
            
            if not deals:
                logger.info("ℹ️ No new deals found")
                return 0
            
            # Validate all affiliate links before posting
            async with LinkValidator() as validator:
                affiliate_links = [self.config.get_affiliate_link(deal.link) for deal in deals]
                validation_results = await validator.validate_links_batch(affiliate_links)
                
                # Log validation statistics
                stats = validator.get_validation_stats(validation_results)
                logger.info(f"🔗 Link validation: {stats['valid_links']}/{stats['total_links']} valid ({stats['success_rate']:.1f}%)")
                
                # Filter deals to only include those with valid links
                valid_deals = []
                for deal, result in zip(deals, validation_results):
                    if result.is_valid:
                        valid_deals.append(deal)
                    else:
                        logger.warning(f"❌ Excluding deal with invalid link: {deal.title[:30]}... ({result.error_message})")
            
            if not valid_deals:
                logger.warning("⚠️ No deals with valid links found")
                return 0
            
            posted_count = 0
            content_generator = ContentGenerator(self.config.OPENAI_API_KEY)
            await content_generator.initialize()
            
            for product in valid_deals:
                try:
                    # Check for duplicates posted in last 2 hours only (more lenient)
                    if product.asin and self.db_manager:
                        try:
                            existing = await self.db_manager.get_deal_by_asin(product.asin)
                            if existing and hasattr(existing, 'posted_at') and existing.posted_at:
                                from datetime import datetime, timedelta, timezone
                                now = datetime.now(timezone.utc)
                                # Handle timezone-aware/naive datetime comparison safely
                                if existing.posted_at.tzinfo is None:
                                    posted_time = existing.posted_at.replace(tzinfo=timezone.utc)
                                else:
                                    posted_time = existing.posted_at
                                time_diff = now - posted_time
                                logger.info(f"🔍 Checking duplicate for {product.title[:30]}: posted {time_diff} ago")
                                if time_diff < timedelta(hours=2):
                                    logger.info(f"⏭️ Skipping recent duplicate: {product.title[:30]} (posted {time_diff} ago)")
                                    continue
                                else:
                                    logger.info(f"🔄 Reposting old deal: {product.title[:30]} (posted {time_diff} ago)")
                        except Exception as duplicate_check_error:
                            logger.warning(f"Duplicate check failed for {product.title[:30]}: {duplicate_check_error}")
                            # Continue posting if duplicate check fails
                    
                    # Use validated affiliate link
                    affiliate_link = getattr(product, 'validated_link', self.config.get_affiliate_link(product.link))
                    
                    # Generate content
                    message = await content_generator.generate_telegram_message(
                        product, affiliate_link
                    )
                    
                    # Post to channel if configured
                    if self.config.TELEGRAM_CHANNEL and self.bot and self.bot.bot:
                        try:
                            await self.bot.bot.send_message(
                                chat_id=self.config.TELEGRAM_CHANNEL,
                                text=message,
                                parse_mode="Markdown",
                                disable_web_page_preview=False
                            )
                            logger.info(f"✅ Posted to Telegram: {product.title[:30]}...")
                        except Exception as telegram_error:
                            logger.error(f"Telegram posting error: {telegram_error}")
                            # Continue to save to database even if Telegram fails
                            pass
                    
                    # Save to database
                    if self.db_manager:
                        await self.db_manager.add_deal(
                            product=product,
                            affiliate_link=affiliate_link,
                            source="scraper",
                            content_style="enthusiastic"
                        )
                    
                    posted_count += 1
                    logger.info(f"✅ Posted deal: {product.title[:50]}...")
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error posting deal {product.title}: {e}")
                    continue
            
            await content_generator.close()
            logger.info(f"📢 Posted {posted_count} new deals with validated links")
            return posted_count
            
        except Exception as e:
            logger.error(f"Error posting deals: {e}")
            return 0
    
    async def cleanup(self):
        """Cleanup application resources."""
        try:
            logger.info("🧹 Cleaning up application resources...")
            
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop()
            
            # Close bot
            if self.bot:
                await self.bot.cleanup()
            
            # Close database
            if self.db_manager:
                await self.db_manager.close()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    """Main application entry point."""
    app = DealBotApplication()
    
    try:
        # Initialize application
        if not await app.initialize():
            logger.error("❌ Failed to initialize application")
            return 1
        
        # Check command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == "bot":
                await app.start_bot_only()
            elif mode == "web":
                await app.start_web_only()
            elif mode == "test":
                await app.test_mode()
            elif mode == "post":
                count = await app.post_deals()
                print(f"Posted {count} deals")
            else:
                logger.error(f"Unknown mode: {mode}")
                return 1
        else:
            # Default: hybrid mode
            await app.start_hybrid_mode()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        return 1
    finally:
        await app.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
