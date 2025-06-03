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

"""This file contains tools for inspecting BigQuery job details."""

from collections import defaultdict

from google.adk.tools import ToolContext
from google.cloud import bigquery
from google.cloud.bigquery.table import TableReference

# This assumes a single, shared client for consistency with your example.
bq_client = None

def get_bq_client(project_id: str = None):
    """Get or initialize the BigQuery client."""
    global bq_client
    if bq_client is None:
        # The project_id can be passed or inferred from the environment.
        bq_client = bigquery.Client(project=project_id)
    return bq_client

def _format_table_ref(table_ref: TableReference) -> str:
    """Helper function to format a TableReference object into a standard string."""
    if not table_ref:
        return "N/A"
    return f"{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}"

def get_job_details(
    job_id: str,
    project_id: str,
    location: str = "us",
    tool_context: ToolContext = None, # tool_context is optional here but good practice
) -> str:
    """
    Retrieves detailed information for a specific BigQuery job ID and returns
    it as a formatted string. This includes the query text, referenced tables,
    query plan, and any performance insights.

    Args:
        job_id: The ID of the BigQuery job to inspect.
        project_id: The Google Cloud project where the job was run.
        location: The location where the job was run (e.g., 'us', 'eu').
        tool_context: The ADK tool context.

    Returns:
        A formatted string containing all the job details.
    """
    client = get_bq_client(project_id)
    job = client.get_job(job_id, location=location)

    # Instead of printing, we'll build a list of strings.
    output_lines = []

    # --- Query Information ---
    output_lines.append("--- Query Information ---")
    output_lines.append(f"Query Text:\n{job.query}")

    if job.referenced_tables:
        output_lines.append("\nReferenced Tables:")
        for table in job.referenced_tables:
            output_lines.append(f"  - {_format_table_ref(table)}")
    else:
        output_lines.append("\nReferenced Tables: None")

    # --- Performance Insights ---
    stage_insights = defaultdict(list)
    if hasattr(job, 'performance_insights') and job.performance_insights:
        output_lines.append("\nPerformance insights found. Mapping them to stages...")
        for insight in job.performance_insights.stage_performance_standalone_insights:
            stage_insights[insight.stage_id].append(insight.insight)
    else:
        output_lines.append("\nNo performance insights were generated for this job.")

    # --- Query Plan ---
    if not job.query_plan:
        output_lines.append("Job has no query plan.")
    else:
        output_lines.append("\n--- Query Execution Plan & Insights ---")
        for stage in job.query_plan:
            output_lines.append(f"\n## Stage {stage.entry_id}: {stage.name}")
            output_lines.append(f"   Status: {stage.status}")
            output_lines.append(f"   Records Read: {stage.records_read:,}")
            output_lines.append(f"   Records Written: {stage.records_written:,}")
            output_lines.append(f"   Slot Time (ms): {stage.slot_ms:,}")

            if stage.entry_id in stage_insights:
                output_lines.append("   *** Query Insights for this stage: ***")
                for insight in stage_insights[stage.entry_id]:
                    output_lines.append(f"     - Type: {insight.insight_type}")
                    if insight.insight_type == "SLOT_CONTENTION":
                        output_lines.append(f"       Contended Slots: {insight.slot_contention.contended_slots_count}")

    # Join all the collected lines into a single string and return it.
    return "\n".join(output_lines)