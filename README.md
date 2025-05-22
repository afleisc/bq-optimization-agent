# BQ Optimization Agent

You need an existing Google Cloud account and a project.
1. Set up a Google Cloud project
2. Set up the gcloud CLI
3. Authenticate to Google Cloud, from the terminal by running `gcloud auth login`.
4. Enable the [Vertex AI API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com).

## Prerequisites

The agent assumes you have already extracted top query hashes with their corresponding SQL text
located in a dataset called `optimization_workshop` and a table called `queries_grouped_by_hash_project`.

1. Run the query below:

```
DECLARE num_days_to_scan INT64 DEFAULT 30;

CREATE TEMP FUNCTION num_stages_with_perf_insights(query_info ANY TYPE) AS (
  COALESCE((
    SELECT SUM(IF(i.slot_contention, 1, 0) + IF(i.insufficient_shuffle_quota, 1, 0))
    FROM UNNEST(query_info.performance_insights.stage_performance_standalone_insights) i), 0)
  + COALESCE(ARRAY_LENGTH(query_info.performance_insights.stage_performance_change_insights), 0)
);

CREATE SCHEMA IF NOT EXISTS optimization_workshop;
CREATE OR REPLACE TABLE optimization_workshop.queries_grouped_by_hash_project AS
WITH JobData AS (
  SELECT
    statement_type,
    query_info.query_hashes.normalized_literals AS query_hash,
    project_id,
    reservation_id,
    query_info,
    job_id,
    parent_job_id,
    query,
    total_slot_ms,
    total_bytes_processed,
    user_email,
    start_time,
    end_time,
    labels,
    referenced_tables,
    creation_time,
    ROW_NUMBER() OVER (PARTITION BY query_info.query_hashes.normalized_literals ORDER BY total_slot_ms DESC) as rn
  FROM
    `region-us`.INFORMATION_SCHEMA.JOBS
  WHERE
    DATE(creation_time) >= CURRENT_DATE - num_days_to_scan
    AND state = 'DONE'
    AND error_result IS NULL
    AND job_type = 'QUERY'
    AND statement_type != 'SCRIPT'
    -- Add this condition to filter out jobs referencing INFORMATION_SCHEMA
    AND NOT EXISTS (
      SELECT 1
      FROM UNNEST(referenced_tables) AS ref_table
      WHERE
        ref_table.dataset_id = 'INFORMATION_SCHEMA'
        OR STARTS_WITH(ref_table.table_id, 'INFORMATION_SCHEMA.')
    )
)
SELECT
  statement_type,
  query_hash,
  COUNT(DISTINCT DATE(start_time)) AS days_active,
  ARRAY_AGG(DISTINCT project_id IGNORE NULLS) AS project_ids,
  ARRAY_AGG(DISTINCT reservation_id IGNORE NULLS) AS reservation_ids,
  SUM(num_stages_with_perf_insights(query_info)) AS num_stages_with_perf_insights,
  COUNT(DISTINCT (project_id || ':us.' || job_id)) AS job_count,
  ANY_VALUE(CASE WHEN rn = 1 THEN query ELSE NULL END) AS top_job_query_text,
  ARRAY_AGG(DISTINCT user_email) AS user_emails,
  SUM(total_bytes_processed) / POW(1024, 3) AS total_gigabytes_processed,
  AVG(total_bytes_processed) / POW(1024, 3) AS avg_gigabytes_processed,
  SUM(total_slot_ms) / (1000 * 60 * 60) AS total_slot_hours,
  AVG(total_slot_ms) / (1000 * 60 * 60) AS avg_total_slot_hours_per_active_day,
  AVG(TIMESTAMP_DIFF(end_time, start_time, SECOND) ) AS avg_job_duration_seconds,
  ARRAY_AGG(DISTINCT FORMAT("%T",labels)) AS labels,
  SUM(total_slot_ms / TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)) AS total_slots,
  AVG(total_slot_ms / TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)) AS avg_total_slots,
  ANY_VALUE(ARRAY(
    SELECT
      ref_table.project_id || '.' ||
      IF(STARTS_WITH(ref_table.dataset_id, '_'), 'TEMP', ref_table.dataset_id)
      || '.' || ref_table.table_id
    FROM UNNEST(referenced_tables) ref_table
  )) AS referenced_tables,
FROM JobData
GROUP BY statement_type, query_hash;
```

## Setup
1. `pip install uv`
2. `chmod +x setup_and_run.sh`
3. `./setup_and_run.sh`

It will prompt you for your GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION if the .env file doesn't exist.

👉 Next Steps (Run these in separate terminals):
   1. Terminal 1 (Toolbox): `./toolbox --tools-file \"tools.yaml\"`
   2. Terminal 2 (Antipattern Tool): `cd bigquery-antipattern-recognition && mvn org.springframework.boot:spring-boot-maven-plugin:run`
   3. Terminal 3 (ADK): `adk web`

