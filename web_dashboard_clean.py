"""
Production Web Dashboard for Amazon Affiliate Deal Bot.
Real-time data with zero demo/mock content - Academic level implementation.
"""
import os
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from config import Config
from database import DatabaseManager
from database_simple import SimpleDatabaseManager

logger = logging.getLogger(__name__)


class AsyncDataManager:
    """Async data manager with sync wrapper for Flask."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_manager = None
        self._loop = None
        self._thread = None
        self._initialized = False
        
    def start(self):
        """Start async event loop in separate thread."""
        if self._initialized:
            return
            
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Wait for initialization
        import time
        timeout = 10
        start_time = time.time()
        while not self._initialized and time.time() - start_time < timeout:
            time.sleep(0.1)
        
    def _run_loop(self):
        """Run async event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Initialize database manager - prefer PostgreSQL if available
            if hasattr(self.config, 'DATABASE_URL') and self.config.DATABASE_URL:
                try:
                    from database import DatabaseManager
                    self.db_manager = DatabaseManager(self.config.DATABASE_URL)
                    logger.info("📊 Dashboard using PostgreSQL database")
                except Exception as e:
                    logger.warning(f"PostgreSQL failed, using in-memory database: {e}")
                    self.db_manager = SimpleDatabaseManager()
            else:
                logger.info("📊 Dashboard using in-memory database")
                self.db_manager = SimpleDatabaseManager()
                
            # Initialize in the loop
            self._loop.run_until_complete(self.db_manager.initialize())
            self._initialized = True
            
            # Keep loop running
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"Error in async loop: {e}")
            self._initialized = True
        
    def execute_async(self, coro):
        """Execute async coroutine and return result."""
        if not self._loop or not self._initialized:
            return None
            
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Async execution error: {e}")
            return None


def safe_int(value, default=0):
    """Safely convert value to int."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def create_app(config: Config):
    """Create production Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = getattr(config, 'FLASK_SECRET_KEY', 'dev-key-change-in-production')
    
    # Initialize async data manager
    data_manager = AsyncDataManager(config)
    data_manager.start()
    
    # Store data manager reference
    setattr(app, 'data_manager', data_manager)
    
    @app.route('/')
    def dashboard():
        """Main dashboard interface."""
        return render_template('dashboard.html')
    
    @app.route('/deals')
    def deals_page():
        """Deals management interface."""
        return render_template('deals.html')
    
    @app.route('/users')
    def users_page():
        """User analytics interface."""
        return render_template('users.html')
    
    @app.route('/api/stats')
    def api_stats():
        """Real-time statistics API endpoint - ONLY REAL DATA with proper error handling."""
        try:
            data_manager = getattr(app, 'data_manager', None)
            if not data_manager or not data_manager.db_manager:
                return jsonify({
                    'error': 'Database not available',
                    'total_deals': 0,
                    'recent_deals': 0,
                    'total_clicks': 0,
                    'total_conversions': 0,
                    'total_earnings': 0.0,
                    'active_users': 0,
                    'conversion_rate': 0.0,
                    'avg_earnings_per_deal': 0.0,
                    'avg_earnings_per_click': 0.0,
                    'category_stats': {},
                    'source_stats': {},
                    'timestamp': datetime.now().isoformat()
                }), 200  # Return 200 instead of 503 to prevent frontend errors
            
            # Initialize default values
            total_deals = 0
            recent_count = 0
            total_clicks = 0
            total_conversions = 0
            total_earnings = 0.0
            active_count = 0
            category_stats = {}
            source_stats = {}
            
            # Get real stats from database with comprehensive error handling
            try:
                stats = data_manager.execute_async(data_manager.db_manager.get_deal_stats())
                if stats:
                    total_deals = safe_int(getattr(stats, 'total_deals', 0))
                    total_clicks = safe_int(getattr(stats, 'total_clicks', 0))
                    total_conversions = safe_int(getattr(stats, 'total_conversions', 0))
                    total_earnings = safe_float(getattr(stats, 'total_earnings', 0.0))
                    recent_count = safe_int(getattr(stats, 'recent_deals', 0))
                    active_count = safe_int(getattr(stats, 'active_users', 0))
                    
                    # Safely get category and source stats
                    category_stats = getattr(stats, 'category_stats', {}) or {}
                    source_stats = getattr(stats, 'source_stats', {}) or {}
                    # Ensure they are dictionaries
                    if not isinstance(category_stats, dict):
                        category_stats = {}
                    if not isinstance(source_stats, dict):
                        source_stats = {}
                    # Clean up None values in stats dicts
                    category_stats = {str(k): int(v) if v is not None else 0 for k, v in category_stats.items()}
                    source_stats = {str(k): int(v) if v is not None else 0 for k, v in source_stats.items()}
                        
            except Exception as e:
                logger.error(f"Error getting deal stats: {e}")
                import traceback
                logger.error(f"Stats traceback: {traceback.format_exc()}")
            
            # Get recent deals count with error handling (fallback if not in stats)
            if recent_count == 0:
                try:
                    recent_deals = data_manager.execute_async(
                        data_manager.db_manager.get_recent_deals(hours=24, limit=100)
                    )
                    recent_count = len(recent_deals) if recent_deals else 0
                except Exception as e:
                    logger.error(f"Error getting recent deals: {e}")
            
            # Get active users count with error handling (fallback if not in stats)
            if active_count == 0:
                try:
                    active_users = data_manager.execute_async(
                        data_manager.db_manager.get_active_users(days=30)
                    )
                    active_count = len(active_users) if active_users else 0
                except Exception as e:
                    logger.error(f"Error getting active users: {e}")
            
            # Calculate conversion rate safely
            conversion_rate = 0.0
            if total_clicks > 0:
                conversion_rate = (total_conversions / total_clicks) * 100
            
            # Calculate averages safely
            avg_earnings_per_deal = 0.0
            avg_earnings_per_click = 0.0
            
            if total_deals > 0:
                avg_earnings_per_deal = total_earnings / total_deals
            
            if total_clicks > 0:
                avg_earnings_per_click = total_earnings / total_clicks
            
            return jsonify({
                'total_deals': total_deals,
                'recent_deals': recent_count,
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'total_earnings': round(total_earnings, 2),
                'active_users': active_count,
                'conversion_rate': round(conversion_rate, 2),
                'avg_earnings_per_deal': round(avg_earnings_per_deal, 2),
                'avg_earnings_per_click': round(avg_earnings_per_click, 4),
                'category_stats': category_stats,
                'source_stats': source_stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Stats API error: {e}")
            import traceback
            logger.error(f"Stats API traceback: {traceback.format_exc()}")
            
            # Return safe default stats with 200 status
            return jsonify({
                'error': 'Statistics temporarily unavailable',
                'total_deals': 0,
                'recent_deals': 0,
                'total_clicks': 0,
                'total_conversions': 0,
                'total_earnings': 0.0,
                'active_users': 0,
                'conversion_rate': 0.0,
                'avg_earnings_per_deal': 0.0,
                'avg_earnings_per_click': 0.0,
                'category_stats': {},
                'source_stats': {},
                'timestamp': datetime.now().isoformat()
            }), 200
    
    @app.route('/api/deals')
    def api_deals():
        """Live deals API endpoint - ONLY REAL DATA."""
        try:
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 50, type=int)
            category = request.args.get('category', None)
            
            data_manager = getattr(app, 'data_manager', None)
            if not data_manager or not data_manager.db_manager:
                return jsonify([])
            
            # Get real deals from database
            deals = data_manager.execute_async(
                data_manager.db_manager.get_recent_deals(
                    hours=hours, limit=limit, category=category
                )
            )
            
            if not deals:
                return jsonify([])
            
            # Convert deals to API format with safe attribute access
            deals_data = []
            for deal in deals:
                try:
                    deal_dict = {
                        'id': getattr(deal, 'id', None),
                        'title': str(getattr(deal, 'title', '') or ''),
                        'price': str(getattr(deal, 'price', '') or ''),
                        'discount': str(getattr(deal, 'discount', '') or ''),
                        'category': str(getattr(deal, 'category', '') or ''),
                        'source': str(getattr(deal, 'source', '') or ''),
                        'asin': str(getattr(deal, 'asin', '') or ''),
                        'clicks': safe_int(getattr(deal, 'clicks', 0)),
                        'conversions': safe_int(getattr(deal, 'conversions', 0)),
                        'earnings': safe_float(getattr(deal, 'earnings', 0.0)),
                        'posted_at': getattr(deal, 'posted_at', None).isoformat() if getattr(deal, 'posted_at', None) else None,
                        'affiliate_link': str(getattr(deal, 'affiliate_link', '') or ''),
                        'rating': safe_float(getattr(deal, 'rating', 0.0)),
                        'review_count': safe_int(getattr(deal, 'review_count', 0)),
                        'is_active': bool(getattr(deal, 'is_active', True))
                    }
                    deals_data.append(deal_dict)
                except Exception as e:
                    logger.error(f"Error processing deal: {e}")
                    continue
            
            return jsonify(deals_data)
            
        except Exception as e:
            logger.error(f"Deals API error: {e}")
            return jsonify([])
    
    @app.route('/api/users')
    def api_users():
        """Live user analytics API endpoint - ONLY REAL DATA."""
        try:
            days = request.args.get('days', 30, type=int)
            
            data_manager = getattr(app, 'data_manager', None)
            if not data_manager or not data_manager.db_manager:
                return jsonify([])
            
            # Get real users from database
            users = data_manager.execute_async(
                data_manager.db_manager.get_active_users(days=days)
            )
            
            if not users:
                return jsonify([])
            
            # Convert users to API format with safe attribute access
            users_data = []
            for user in users:
                try:
                    user_dict = {
                        'id': getattr(user, 'id', None),
                        'user_id': safe_int(getattr(user, 'user_id', 0)),
                        'username': getattr(user, 'username', None),
                        'first_name': getattr(user, 'first_name', None),
                        'last_name': getattr(user, 'last_name', None),
                        'category': str(getattr(user, 'category', 'all') or 'all'),
                        'region': str(getattr(user, 'region', 'US') or 'US'),
                        'total_clicks': safe_int(getattr(user, 'total_clicks', 0)),
                        'total_conversions': safe_int(getattr(user, 'total_conversions', 0)),
                        'total_earnings': safe_float(getattr(user, 'total_earnings', 0.0)),
                        'joined_at': getattr(user, 'joined_at', None).isoformat() if getattr(user, 'joined_at', None) else None,
                        'last_seen': getattr(user, 'last_seen', None).isoformat() if getattr(user, 'last_seen', None) else None,
                        'is_active': bool(getattr(user, 'is_active', True))
                    }
                    users_data.append(user_dict)
                except Exception as e:
                    logger.error(f"Error processing user: {e}")
                    continue
            
            return jsonify(users_data)
            
        except Exception as e:
            logger.error(f"Users API error: {e}")
            return jsonify([])
    
    @app.route('/api/config')
    def api_config():
        """Configuration API endpoint."""
        try:
            return jsonify({
                'affiliate_id': config.AFFILIATE_ID,
                'supported_regions': config.get_supported_regions() if hasattr(config, 'get_supported_regions') else ['US'],
                'default_region': getattr(config, 'DEFAULT_REGION', 'US'),
                'bot_configured': getattr(config, 'bot_configured', False),
                'openai_configured': getattr(config, 'openai_configured', False),
                'database_configured': getattr(config, 'database_configured', False),
                'post_interval_hours': getattr(config, 'POST_INTERVAL_HOURS', 1),
                'version': '2.0.0-production'
            })
        except Exception as e:
            logger.error(f"Config API error: {e}")
            return jsonify({'error': 'Configuration unavailable'}), 500
    
    @app.route('/api/health')
    def api_health():
        """Health check endpoint."""
        try:
            data_manager = getattr(app, 'data_manager', None)
            db_healthy = False
            
            if data_manager and hasattr(data_manager, 'db_manager') and data_manager.db_manager is not None:
                # Test database connection
                if hasattr(data_manager, 'execute_async'):
                    try:
                        test_stats = data_manager.execute_async(data_manager.db_manager.get_deal_stats())
                        db_healthy = test_stats is not None
                    except:
                        db_healthy = False
                else:
                    db_healthy = True  # Simple database manager
            
            return jsonify({
                'status': 'healthy' if db_healthy else 'degraded',
                'database': 'connected' if db_healthy else 'disconnected',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)  
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def run_production_dashboard():
    """Run the production dashboard."""
    config = Config()
    app = create_app(config)
    
    logger.info("Starting production web dashboard on http://0.0.0.0:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_production_dashboard()
