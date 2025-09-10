#!/usr/bin/env python3
"""
Summarize materialized view refresh logs for reporting
"""

import sys
import re
from collections import defaultdict
from datetime import datetime

def parse_log_file(log_file):
    """Parse refresh log and extract statistics"""
    stats = {
        'total_refreshes': 0,
        'successful_refreshes': 0,
        'failed_refreshes': 0,
        'view_stats': defaultdict(lambda: {'success': 0, 'failed': 0, 'total_time': 0}),
        'errors': [],
        'date_range': {'start': None, 'end': None}
    }
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # Extract timestamp
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    if not stats['date_range']['start'] or timestamp < stats['date_range']['start']:
                        stats['date_range']['start'] = timestamp
                    if not stats['date_range']['end'] or timestamp > stats['date_range']['end']:
                        stats['date_range']['end'] = timestamp
                
                # Check for successful refresh
                success_match = re.search(r'Successfully refreshed (\w+) in ([\d.]+)s', line)
                if success_match:
                    view_name = success_match.group(1)
                    duration = float(success_match.group(2))
                    stats['successful_refreshes'] += 1
                    stats['view_stats'][view_name]['success'] += 1
                    stats['view_stats'][view_name]['total_time'] += duration
                
                # Check for failed refresh
                fail_match = re.search(r'Failed to refresh (\w+): (.+)', line)
                if fail_match:
                    view_name = fail_match.group(1)
                    error = fail_match.group(2)
                    stats['failed_refreshes'] += 1
                    stats['view_stats'][view_name]['failed'] += 1
                    stats['errors'].append({
                        'view': view_name,
                        'error': error,
                        'timestamp': timestamp if 'timestamp' in locals() else None
                    })
                
                # Check for refresh complete
                if 'Refresh complete:' in line:
                    stats['total_refreshes'] += 1
                    
    except Exception as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        return None
    
    return stats

def generate_summary(stats):
    """Generate a summary report"""
    if not stats:
        return "No statistics available"
    
    summary = []
    summary.append("=== Materialized View Refresh Summary ===")
    
    if stats['date_range']['start'] and stats['date_range']['end']:
        summary.append(f"Period: {stats['date_range']['start']} to {stats['date_range']['end']}")
    
    summary.append(f"\nTotal refresh cycles: {stats['total_refreshes']}")
    summary.append(f"Successful refreshes: {stats['successful_refreshes']}")
    summary.append(f"Failed refreshes: {stats['failed_refreshes']}")
    
    if stats['successful_refreshes'] > 0:
        success_rate = (stats['successful_refreshes'] / (stats['successful_refreshes'] + stats['failed_refreshes'])) * 100
        summary.append(f"Success rate: {success_rate:.1f}%")
    
    summary.append("\n=== Per-View Statistics ===")
    for view_name, view_stat in sorted(stats['view_stats'].items()):
        success_count = view_stat['success']
        failed_count = view_stat['failed']
        total_count = success_count + failed_count
        
        if success_count > 0:
            avg_time = view_stat['total_time'] / success_count
            summary.append(f"\n{view_name}:")
            summary.append(f"  Refreshes: {total_count} (Success: {success_count}, Failed: {failed_count})")
            summary.append(f"  Average time: {avg_time:.2f}s")
        else:
            summary.append(f"\n{view_name}:")
            summary.append(f"  All {total_count} refreshes failed")
    
    if stats['errors']:
        summary.append("\n=== Recent Errors ===")
        for error in stats['errors'][-10:]:  # Last 10 errors
            summary.append(f"{error['timestamp']}: {error['view']} - {error['error']}")
    
    return '\n'.join(summary)

def main():
    if len(sys.argv) < 2:
        print("Usage: summarize_refresh_log.py <log_file>", file=sys.stderr)
        sys.exit(1)
    
    log_file = sys.argv[1]
    stats = parse_log_file(log_file)
    
    if stats:
        summary = generate_summary(stats)
        print(summary)
        
        # Optionally save to file
        summary_file = log_file.replace('.log', '_summary.txt')
        try:
            with open(summary_file, 'w') as f:
                f.write(summary)
            print(f"\nSummary saved to: {summary_file}")
        except Exception as e:
            print(f"Could not save summary: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()