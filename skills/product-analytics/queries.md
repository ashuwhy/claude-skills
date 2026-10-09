# PostHog queries

Run through the PostHog MCP: `exec` with `call execute-sql {"query": "..."}`. The dialect is HogQL, so `properties.$x` reads an event property. Property and table names are as of *(checked 2026-10)*; if a query errors, look the schema up with `read-data-schema` and fix the query here.

## Did it arrive

```sql
SELECT event, timestamp, properties.$os, properties.$app_version
FROM events
WHERE timestamp > now() - INTERVAL 20 MINUTE
ORDER BY timestamp DESC
LIMIT 50
```

## Exceptions

```sql
SELECT timestamp, properties.$device_name, properties.$app_version,
       properties.$exception_types, properties.$exception_values
FROM events
WHERE event = '$exception' AND timestamp > now() - INTERVAL 14 DAY
ORDER BY timestamp DESC
```

Query the flattened `$exception_types` and `$exception_values`. `$exception_list` is a nullable JSON blob that array functions choke on.

## Tester devices per day

A device here is a model and OS-version pair, so two testers on the same model count once: treat these as floors. Exclude my own devices and emulators by name.

```sql
SELECT toDate(timestamp) AS day,
       count(DISTINCT concat(toString(properties.$device_name), '|', toString(properties.$os_version))) AS devices
FROM events
WHERE properties.$os = 'Android' AND timestamp >= '<closed test start>'
  AND properties.$device_name NOT IN ('<my phone>', '<emulator>')
GROUP BY day ORDER BY day
```

Variations a production-access application needs:
- days active per device: group by the pair, `count(DISTINCT toDate(timestamp))`, then count devices above a threshold.
- took an update from the store: devices with more than one distinct `properties.$app_version`.
- feature reach: distinct pairs per event name.

## Cold start

The cold-start span carries the device tier. Report p50 and p90 by tier, before and after a release, a week after it ships, and record the baseline in the app's repo.

Traces live in their own table, not `events`. Look the table and columns up with `read-data-schema` first, then take `quantile(0.5)` and `quantile(0.9)` of duration grouped by the tier attribute. Drop spans with clock-skew durations (negative or days long). Once a query works, save it here.
