#!/bin/bash
#
# Check for materialized view refresh failures and send alerts
# This script should be run periodically (e.g., every hour) via cron
#

# Configuration
LOG_FILE="/var/log/rpx/refresh.log"
STATE_FILE="/var/run/rpx/last_refresh_check"
ALERT_EMAIL="devops@rpx.com"
WEBHOOK_URL="${RPX_WEBHOOK_URL:-}"  # Set in environment
MAX_AGE_HOURS=6  # Alert if no successful refresh in this many hours

# Create state directory if needed
mkdir -p /var/run/rpx

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    
    # Send email if configured
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
    fi
    
    # Send to webhook if configured
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"🚨 $subject\\n$message\"}" \
            2>/dev/null
    fi
    
    # Always log
    logger -t "rpx-refresh-monitor" "$subject: $message"
}

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    send_alert "RPX MV Refresh: Log Missing" "Log file not found: $LOG_FILE"
    exit 1
fi

# Check for recent failures
RECENT_FAILURES=$(grep -E "Failed to refresh|ERROR" "$LOG_FILE" | tail -20)
if [ -n "$RECENT_FAILURES" ]; then
    # Check if we already alerted for these failures
    if [ -f "$STATE_FILE" ]; then
        LAST_CHECK=$(cat "$STATE_FILE")
        NEW_FAILURES=$(echo "$RECENT_FAILURES" | grep -v "$LAST_CHECK" || true)
    else
        NEW_FAILURES="$RECENT_FAILURES"
    fi
    
    if [ -n "$NEW_FAILURES" ]; then
        send_alert "RPX MV Refresh: Failures Detected" "Recent failures:\\n$NEW_FAILURES"
        echo "$RECENT_FAILURES" > "$STATE_FILE"
    fi
fi

# Check for stale data (no successful refresh in MAX_AGE_HOURS)
LAST_SUCCESS=$(grep -E "Successfully refreshed|Refresh complete.*successful" "$LOG_FILE" | tail -1)
if [ -n "$LAST_SUCCESS" ]; then
    # Extract timestamp (assuming standard log format)
    LAST_TIMESTAMP=$(echo "$LAST_SUCCESS" | cut -d' ' -f1-2)
    
    # Convert to seconds since epoch
    if command -v gdate &> /dev/null; then
        # macOS with GNU date
        LAST_EPOCH=$(gdate -d "$LAST_TIMESTAMP" +%s 2>/dev/null || echo "0")
        CURRENT_EPOCH=$(gdate +%s)
    else
        # Linux
        LAST_EPOCH=$(date -d "$LAST_TIMESTAMP" +%s 2>/dev/null || echo "0")
        CURRENT_EPOCH=$(date +%s)
    fi
    
    # Calculate age in hours
    AGE_HOURS=$(( (CURRENT_EPOCH - LAST_EPOCH) / 3600 ))
    
    if [ "$AGE_HOURS" -gt "$MAX_AGE_HOURS" ]; then
        send_alert "RPX MV Refresh: Stale Data Warning" \
            "No successful refresh in $AGE_HOURS hours. Last success: $LAST_TIMESTAMP"
    fi
else
    send_alert "RPX MV Refresh: No Success Found" \
        "No successful refresh found in log file"
fi

# Check materialized view status via Python script
STATUS_OUTPUT=$(/usr/bin/python3 /opt/rpx-backend/scripts/refresh_materialized_views.py --check-only 2>&1)
UNPOPULATED=$(echo "$STATUS_OUTPUT" | grep -E '"populated": false' || true)

if [ -n "$UNPOPULATED" ]; then
    send_alert "RPX MV Refresh: Unpopulated Views" \
        "Some materialized views are not populated:\\n$UNPOPULATED"
fi

# Update check timestamp
date > "$STATE_FILE.timestamp"

exit 0