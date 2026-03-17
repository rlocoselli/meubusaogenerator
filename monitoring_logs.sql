-- Monitoring queries for import logs (PostgreSQL)
-- Assumes table: log(id, level, message, timestamp)

-- 1) Volume by day and level
SELECT
    date_trunc('day', "timestamp") AS day,
    level,
    COUNT(*) AS total
FROM log
GROUP BY 1, 2
ORDER BY 1 DESC, 2;


-- 2) Last 100 errors and warnings
SELECT
    id,
    "timestamp",
    level,
    message
FROM log
WHERE level IN ('ERROR', 'WARNING')
ORDER BY "timestamp" DESC
LIMIT 100;


-- 3) Error/Warning counts by dataset (if message starts with [dataset])
WITH parsed AS (
    SELECT
        "timestamp",
        level,
        message,
        CASE
            WHEN message ~ '^\[[^]]+\]' THEN substring(message FROM '^\[([^]]+)\]')
            ELSE 'unknown'
        END AS dataset
    FROM log
)
SELECT
    dataset,
    level,
    COUNT(*) AS total
FROM parsed
WHERE level IN ('ERROR', 'WARNING')
GROUP BY dataset, level
ORDER BY dataset, level;


-- 4) Daily import health summary
SELECT
    date_trunc('day', "timestamp") AS day,
    COUNT(*) FILTER (WHERE level = 'INFO' AND message ILIKE 'Import succeeded%') AS success,
    COUNT(*) FILTER (WHERE level = 'INFO' AND message ILIKE 'Import completed with warnings%') AS success_with_warnings,
    COUNT(*) FILTER (WHERE level = 'ERROR' AND message ILIKE 'Import failed%') AS failed,
    COUNT(*) FILTER (WHERE level = 'WARNING') AS warnings
FROM log
GROUP BY 1
ORDER BY 1 DESC;


-- 5) Most frequent warning messages (deduplicated by exact text)
SELECT
    message,
    COUNT(*) AS total
FROM log
WHERE level = 'WARNING'
GROUP BY message
ORDER BY total DESC, message
LIMIT 20;


-- 6) Last import status by dataset
WITH parsed AS (
    SELECT
        id,
        "timestamp",
        level,
        message,
        CASE
            WHEN message ~ '^\[[^]]+\]' THEN substring(message FROM '^\[([^]]+)\]')
            WHEN message ILIKE 'Import % for %' THEN split_part(message, ' for ', 2)
            ELSE 'unknown'
        END AS dataset
    FROM log
),
ranked AS (
    SELECT
        dataset,
        level,
        message,
        "timestamp",
        ROW_NUMBER() OVER (PARTITION BY dataset ORDER BY "timestamp" DESC, id DESC) AS rn
    FROM parsed
)
SELECT
    dataset,
    level,
    message,
    "timestamp"
FROM ranked
WHERE rn = 1
ORDER BY dataset;
