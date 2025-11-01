import os
import time
import json
import requests
from collections import deque

LOG_PATH = "/var/log/nginx/access.log"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "200") or 200)
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", "2") or 2)
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", "300") or 300)

errors = deque(maxlen=WINDOW_SIZE)
last_pool = None
last_alert_time = {"failover": 0, "error_rate": 0}

def send_slack_alert(message, alert_type="general"):
    global last_alert_time
    if not SLACK_WEBHOOK_URL:
        print("❌ No Slack webhook URL provided. Alert skipped:", message)
        return

    if time.time() - last_alert_time.get(alert_type, 0) < ALERT_COOLDOWN_SEC:
        print(f"⏰ Alert cooldown active for {alert_type}. Skipping:", message)
        return
    
    last_alert_time[alert_type] = time.time()
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        if response.status_code == 200:
            print("✅ Slack alert sent:", message)
        else:
            print(f"❌ Slack alert failed with status {response.status_code}:", message)
    except Exception as e:
        print("❌ Failed to send Slack alert:", e)

def parse_pool_from_upstream(upstream_addr):
    """Extract pool name from upstream address, handling multiple upstreams"""
    if not upstream_addr or upstream_addr == "-":
        return None
    
    # When failover happens, upstream_addr contains multiple addresses like:
    # "172.18.0.3:3000, 172.18.0.2:3000"
    # The LAST address is the one that actually served the request
    
    # Split by comma and take the last address (the successful one)
    addresses = [addr.strip() for addr in upstream_addr.split(',')]
    actual_upstream = addresses[-1] if addresses else upstream_addr
    
    # Map IP addresses to pools
    # 172.18.0.2:3000 = green
    # 172.18.0.3:3000 = blue
    if "app_blue" in actual_upstream or "172.18.0.3:" in actual_upstream:
        return "blue"
    elif "app_green" in actual_upstream or "172.18.0.2:" in actual_upstream:
        return "green"
    
    return None

def analyze_log(line):
    global last_pool
    
    if not line.strip().startswith('{'):
        return
    
    try:
        data = json.loads(line)
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON: {e}")
        return

    upstream_addr = data.get("pool", "") or data.get("upstream_addr", "")
    upstream_status = str(data.get("upstream_status", "")).strip()
    
    # Parse which pool actually served the request
    pool = parse_pool_from_upstream(upstream_addr)
    
    # Check if multiple upstreams were tried (indicates failover attempt)
    failover_attempted = ',' in upstream_addr
    
    print(f"📝 {data.get('method')} {data.get('uri')} - Status: {data.get('status')} - Upstream: {upstream_addr} - Pool: {pool}{' [FAILOVER]' if failover_attempted else ''}")
    
    # Handle 5xx errors
    is_error = False
    if upstream_status and upstream_status != "-":
        # Handle multiple upstream statuses (e.g., "502, 200")
        statuses = [s.strip() for s in upstream_status.split(',')]
        # Check if ANY status is 5xx
        is_error = any(s.startswith("5") for s in statuses)

    # Detect failover - ONLY if both pools are valid AND different
    if pool and last_pool and pool != last_pool:
        send_slack_alert(
            f"🔄 *Failover Detected!*\n"
            f"Pool switched: `{last_pool}` → `{pool}`\n"
            f"Time: {data.get('time', 'unknown')}\n"
            f"Upstream addresses: {upstream_addr}\n"
            f"Status: {data.get('status')}",
            alert_type="failover"
        )
        print(f"🔔 FAILOVER DETECTED: {last_pool} -> {pool}")
    
    if pool:
        last_pool = pool

    # Track errors
    errors.append(1 if is_error else 0)

    if len(errors) == WINDOW_SIZE:
        error_count = sum(errors)
        rate = (error_count / WINDOW_SIZE) * 100
        if rate > ERROR_RATE_THRESHOLD:
            send_slack_alert(
                f"🚨 *High Error Rate Alert!*\n"
                f"Error Rate: `{rate:.2f}%` ({error_count}/{WINDOW_SIZE} requests)\n"
                f"Threshold: `{ERROR_RATE_THRESHOLD}%`\n"
                f"Current Pool: `{pool or 'unknown'}`\n"
                f"Time: {data.get('time', 'unknown')}",
                alert_type="error_rate"
            )

def tail_logs():
    print(f"🔍 Waiting for Nginx log file: {LOG_PATH}")
    while not os.path.exists(LOG_PATH):
        time.sleep(1)
    
    print(f"✅ Log file found. Starting to monitor...")
    print(f"📊 Configuration:")
    print(f"   - Window Size: {WINDOW_SIZE}")
    print(f"   - Error Threshold: {ERROR_RATE_THRESHOLD}%")
    print(f"   - Alert Cooldown: {ALERT_COOLDOWN_SEC}s")
    print(f"   - Slack Webhook: {'Configured ✓' if SLACK_WEBHOOK_URL else 'Not configured ✗'}")
    print("-" * 50)

    with open(LOG_PATH, "r") as f:
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            analyze_log(line.strip())

if __name__ == "__main__":
    print("🚀 Alert Watcher Starting...")
    tail_logs()