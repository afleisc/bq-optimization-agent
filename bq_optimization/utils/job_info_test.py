import json
from collections import defaultdict
from google.cloud import bigquery
from google.cloud.bigquery.job import QueryPlanEntry
from google.cloud.bigquery.table import TableReference

# Ensure you have authenticated correctly
client = bigquery.Client(project="dannydeleo")

def _format_table_ref(table_ref: TableReference) -> str:
    """Helper function to format a TableReference object into a standard string."""
    if not table_ref:
        return "N/A"
    return f"{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}"

def get_job(
    client: bigquery.Client,
    location: str = "us",
    job_id: str = "abcd-efgh-ijkl-mnop",
) -> None:
    """
    Retrieves a BigQuery job and prints its query, tables, and detailed
    statistics for each stage of its query plan.
    """
    print(f"Fetching job {job_id} from location {location}...")
    job = client.get_job(job_id, location=location)

    # --- ADDED SECTION ---
    print("\n--- Query Information ---")
    # Print the original SQL query text
    print(f"Query Text:\n{job.query}")

    # Print the tables referenced in the query
    if job.referenced_tables:
        print("\nReferenced Tables:")
        for table in job.referenced_tables:
            print(f"  - {_format_table_ref(table)}")
    else:
        print("\nReferenced Tables: None")
    # --- END ADDED SECTION ---

    stage_insights = defaultdict(list)
    
    # Use hasattr to safely check if the performance_insights attribute exists
    if hasattr(job, 'performance_insights') and job.performance_insights and job.performance_insights.stage_performance_standalone_insights:
        print("\nPerformance insights found. Mapping them to stages...")
        for insight in job.performance_insights.stage_performance_standalone_insights:
            stage_insights[insight.stage_id].append(insight.insight)
    else:
        # This message will appear if the library is old or if no insights were generated
        print("\nNo performance insights attribute found or no insights were generated for this job.")


    if not job.query_plan:
        print("Job has no query plan.")
        return

    print("\n--- Query Execution Plan & Insights ---")
    for stage in job.query_plan:
        print(f"\n## Stage {stage.entry_id}: {stage.name}")
        print(f"   Status: {stage.status}")
        print(f"   Records Read: {stage.records_read:,}")
        print(f"   Records Written: {stage.records_written:,}")
        print(f"   Slot Time (ms): {stage.slot_ms:,}")

        if stage.entry_id in stage_insights:
            print("   *** Query Insights for this stage: ***")
            for insight in stage_insights[stage.entry_id]:
                print(f"     - Type: {insight.insight_type}")
                if insight.insight_type == "SLOT_CONTENTION":
                    print(f"       Contended Slots: {insight.slot_contention.contended_slots_count}")

# Use the job_id you're interested in
get_job(client, job_id="8e0e63fc-3e75-4d0d-ba71-e9e0fecad2e6")