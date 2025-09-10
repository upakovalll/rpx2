#!/usr/bin/env python3
"""
Automated Materialized View Refresh Script

This script refreshes all materialized views in the correct dependency order.
Can be run manually or scheduled via cron.

Usage:
    python refresh_materialized_views.py [--concurrent] [--notify]
    
Cron example (refresh every 4 hours):
    0 */4 * * * /usr/bin/python3 /path/to/refresh_materialized_views.py --notify
"""

import os
import sys
import time
import logging
import argparse
import psycopg2
from datetime import datetime
from typing import List, Tuple, Dict
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/rpx/materialized_view_refresh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Materialized views in dependency order
MATERIALIZED_VIEWS = {
    'level1': [
        'mv_loan_rpx_adjustments'
    ],
    'level2': [
        'mv_pricing_engine_output_complete'
    ]
}

class MaterializedViewRefresher:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.refresh_results = []
        
    def refresh_view(self, view_name: str, concurrent: bool = False) -> Tuple[bool, float, str]:
        """
        Refresh a single materialized view
        
        Returns:
            Tuple of (success, duration_seconds, error_message)
        """
        start_time = time.time()
        error_message = None
        
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    refresh_cmd = f"REFRESH MATERIALIZED VIEW {'CONCURRENTLY' if concurrent else ''} {view_name}"
                    logger.info(f"Refreshing {view_name}...")
                    cur.execute(refresh_cmd)
                    conn.commit()
                    
            duration = time.time() - start_time
            logger.info(f"✅ Successfully refreshed {view_name} in {duration:.2f}s")
            return True, duration, None
            
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            logger.error(f"❌ Failed to refresh {view_name}: {error_message}")
            return False, duration, error_message
    
    def refresh_all(self, concurrent: bool = False) -> Dict:
        """
        Refresh all materialized views in the correct order
        
        Returns:
            Dictionary with refresh results
        """
        total_start = time.time()
        
        # Get current valuation/settlement dates being used
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            get_valuation_date() as valuation_date,
                            get_settlement_date() as settlement_date
                    """)
                    dates = cur.fetchone()
                    logger.info(f"Refreshing materialized views with valuation_date={dates[0]}, settlement_date={dates[1]}")
        except Exception as e:
            logger.warning(f"Could not get current dates: {e}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'views': [],
            'summary': {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'total_duration': 0
            }
        }
        
        # Refresh Level 1 views
        logger.info("Starting Level 1 materialized view refresh...")
        for view in MATERIALIZED_VIEWS['level1']:
            success, duration, error = self.refresh_view(view, concurrent)
            results['views'].append({
                'name': view,
                'level': 1,
                'success': success,
                'duration': round(duration, 2),
                'error': error
            })
            results['summary']['total'] += 1
            if success:
                results['summary']['successful'] += 1
            else:
                results['summary']['failed'] += 1
        
        # Refresh Level 2 views only if all Level 1 succeeded
        level1_success = all(v['success'] for v in results['views'])
        if level1_success:
            logger.info("Starting Level 2 materialized view refresh...")
            for view in MATERIALIZED_VIEWS['level2']:
                success, duration, error = self.refresh_view(view, concurrent)
                results['views'].append({
                    'name': view,
                    'level': 2,
                    'success': success,
                    'duration': round(duration, 2),
                    'error': error
                })
                results['summary']['total'] += 1
                if success:
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1
        else:
            logger.warning("Skipping Level 2 refresh due to Level 1 failures")
        
        results['summary']['total_duration'] = round(time.time() - total_start, 2)
        return results
    
    def check_view_status(self) -> List[Dict]:
        """Check the status of all materialized views"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            matviewname,
                            ispopulated,
                            pg_size_pretty(pg_total_relation_size(matviewname::regclass)) as size
                        FROM pg_matviews 
                        WHERE matviewname LIKE 'mv_%'
                        ORDER BY matviewname
                    """)
                    
                    return [
                        {
                            'name': row[0],
                            'populated': row[1],
                            'size': row[2]
                        }
                        for row in cur.fetchall()
                    ]
        except Exception as e:
            logger.error(f"Failed to check view status: {e}")
            return []

def send_notification(results: Dict, webhook_url: str = None):
    """Send notification about refresh results"""
    if webhook_url:
        # Send to webhook (Slack, Teams, etc.)
        try:
            import requests
            
            message = f"Materialized View Refresh Complete\n"
            message += f"Total: {results['summary']['total']}\n"
            message += f"Success: {results['summary']['successful']}\n"
            message += f"Failed: {results['summary']['failed']}\n"
            message += f"Duration: {results['summary']['total_duration']}s"
            
            if results['summary']['failed'] > 0:
                message += "\n\nFailed views:\n"
                for view in results['views']:
                    if not view['success']:
                        message += f"- {view['name']}: {view['error']}\n"
            
            # Example for Slack webhook
            requests.post(webhook_url, json={'text': message})
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    # Always log summary
    logger.info(f"Refresh complete: {results['summary']['successful']}/{results['summary']['total']} successful in {results['summary']['total_duration']}s")

def main():
    parser = argparse.ArgumentParser(description='Refresh materialized views')
    parser.add_argument('--concurrent', action='store_true', 
                        help='Use CONCURRENTLY option (requires unique indexes)')
    parser.add_argument('--notify', action='store_true',
                        help='Send notifications on completion')
    parser.add_argument('--webhook-url', type=str,
                        help='Webhook URL for notifications')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check view status, do not refresh')
    
    args = parser.parse_args()
    
    # Get database connection
    settings = get_settings()
    connection_string = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    
    refresher = MaterializedViewRefresher(connection_string)
    
    if args.check_only:
        # Just check status
        status = refresher.check_view_status()
        print(json.dumps(status, indent=2))
        return
    
    # Perform refresh
    logger.info(f"Starting materialized view refresh at {datetime.now()}")
    results = refresher.refresh_all(concurrent=args.concurrent)
    
    # Save results to file
    results_file = f"/var/log/rpx/refresh_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save results file: {e}")
    
    # Send notifications if requested
    if args.notify:
        send_notification(results, args.webhook_url)
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['failed'] == 0 else 1)

if __name__ == "__main__":
    main()