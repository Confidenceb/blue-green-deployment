# Alert Runbook

## Failover Detected Alert

**Message:** `🔄 Failover detected! Pool switched from [old] to [new].`

**Meaning:** Nginx automatically switched from one pool to another, likely due to upstream failures.

**Actions:**

1. Check the health of the failed pool: `docker logs app_[old_pool]`
2. Verify the new pool is serving traffic correctly
3. Investigate why the original pool failed
4. If intentional (deployment), no action needed

## High Error Rate Alert

**Message:** `🚨 High error rate: X.XX% over last N requests.`

**Meaning:** The upstream is returning 5xx errors above the configured threshold.

**Actions:**

1. Check upstream logs: `docker logs app_blue` and `docker logs app_green`
2. Verify application health endpoints
3. Consider manual failover: Update `ACTIVE_POOL` in `.env` and restart nginx
4. Investigate root cause (database, external API, resource exhaustion)

## Suppressing Alerts

During planned maintenance or testing:

1. Temporarily increase `ALERT_COOLDOWN_SEC` in `.env`
2. Or stop the watcher: `docker stop alert_watcher`
3. Resume after maintenance: `docker start alert_watcher`
