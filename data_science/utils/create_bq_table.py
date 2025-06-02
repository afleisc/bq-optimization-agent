# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.cloud import bigquery
from pathlib import Path
from dotenv import load_dotenv

# Define the path to the .env file and load environment variables
env_file_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_file_path)


def run_bigquery_script(client: bigquery.Client, script: str, script_name: str):
    """Executes a multi-statement BigQuery script.

    Args:
        client: The BigQuery client object.
        script: A string containing the BigQuery script to execute.
        script_name: The name of the script for logging purposes.
    """
    print(f"▶️ Running BigQuery script: {script_name}...")
    try:
        # Start the query job.
        query_job = client.query(script)

        # Wait for the job to complete.
        query_job.result()
        print(f"✅ Successfully finished running {script_name}.")

    except Exception as e:
        print(f"❌ An error occurred while running {script_name}: {e}")
        print(f"Failed query:\n---\n{script}\n---")


def main():
    """Main function to execute the BigQuery scripts."""
    project_id = os.getenv("BQ_PROJECT_ID")
    if not project_id:
        raise ValueError("BQ_PROJECT_ID environment variable not set.")

    # Initialize the BigQuery client
    client = bigquery.Client(project=project_id)

    # --- BigQuery Script 1: Aggregate query job statistics ---
    script_1 = """
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
      )) AS referenced_tables
    FROM JobData
    GROUP BY statement_type, query_hash;
    """

    # --- BigQuery Script 2: Extract table DDLs ---
    # Note: Corrected a syntax error (double comma) in the original SELECT statement.
    script_2 = """
    CREATE SCHEMA IF NOT EXISTS optimization_workshop;
    CREATE OR REPLACE TABLE optimization_workshop.table_ddls AS
    SELECT table_catalog, table_schema, table_name, table_type, ddl
    FROM `region-us`.INFORMATION_SCHEMA.TABLES;
    """

    # Execute the scripts sequentially
    run_bigquery_script(client, script_1, "Aggregate Query Statistics")
    run_bigquery_script(client, script_2, "Extract Table DDLs")

    print("\nAll scripts have been executed.")


if __name__ == "__main__":
    main()