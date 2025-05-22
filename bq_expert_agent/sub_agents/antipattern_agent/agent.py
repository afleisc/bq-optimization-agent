from google.adk.agents.llm_agent import LlmAgent
import json
import urllib.request
import urllib.error

# --- Configuration (Optional: move to environment variables or a config file) ---
# Ensure your Spring Boot anti-pattern service is running locally.
ANTI_PATTERN_SERVICE_URL = "http://localhost:8080/analyze-query-ui"

# --- Tool Function Definition ---
def analyze_bigquery_sql_anti_patterns(sql_query: str) -> list: # Changed return type to just list
    """
    Analyzes a BigQuery SQL query for common anti-patterns by calling a local web service.
    The local web service must be running at http://localhost:8080/analyze-query-ui.
    Returns a list of identified anti-patterns (each as a dictionary with 'name' and 'suggestion').
    If no anti-patterns are found by the service, it will typically return a list containing
    a specific object like [{"name": "None", "suggestion": "No anti-patterns found."}].
    If an error occurs within this tool or when calling the service, a list containing a
    single error dictionary (e.g., [{"name": "ToolError", "suggestion": "Error details"}]) is returned.

    Args:
        sql_query (str): The BigQuery SQL query string to be analyzed.

    Returns:
        list: A list of dictionaries. Each dictionary represents an anti-pattern 
              (with "name" and "suggestion" keys) or an error encountered by the tool.
    """
    headers = {
        "Content-Type": "text/plain",
        "Accept": "application/json",
    }
    data = sql_query.encode('utf-8')

    try:
        request = urllib.request.Request(ANTI_PATTERN_SERVICE_URL, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            response_body = response.read().decode('utf-8')
            if response.status == 200:
                try:
                    analysis_results = json.loads(response_body)
                    if isinstance(analysis_results, list):
                        # Service is expected to return a list, e.g.:
                        # [{"name": "AntiPatternName", "suggestion": "Suggestion text"}, ...]
                        # Or [{"name": "None", "suggestion": "No anti-patterns found."}]
                        # Or [{"name": "Error", "suggestion": "Error message from service"}]
                        return analysis_results 
                    else:
                        # Should not happen if service always returns a list as per its contract
                        return [{"name": "ToolError", "suggestion": f"Unexpected response format from service: {analysis_results}"}]

                except json.JSONDecodeError:
                    return [{"name": "ToolError", "suggestion": f"Failed to decode JSON response from the anti-pattern service. Raw response: {response_body}"}]
            else:
                return [{"name": "ToolError", "suggestion": f"Anti-pattern service returned HTTP {response.status}. Response: {response_body}"}]

    except urllib.error.HTTPError as e:
        error_response = e.read().decode(errors='ignore')
        return [{"name": "ToolError", "suggestion": f"Anti-pattern service HTTP error: {e.code} {e.reason}. Details: {error_response}"}]
    except urllib.error.URLError as e:
        return [{"name": "ToolError", "suggestion": f"Could not connect to the anti-pattern service at {ANTI_PATTERN_SERVICE_URL}. Is it running? Details: {e.reason}"}]
    except Exception as e:
        return [{"name": "ToolError", "suggestion": f"An unexpected error occurred while analyzing anti-patterns: {str(e)}"}]

antipattern_agent = LlmAgent(
        model='gemini-2.0-flash', # Or your preferred compatible model
        name='bq_antipattern_agent',
        instruction=(
            "You are an intelligent BigQuery SQL optimization assistant. "
            "When given an SQL query, use the 'analyze_bigquery_sql_anti_patterns' tool "
            "to check for common anti-patterns. Remember to replace '\n' with actual new lines and remove comments so that the query is formatted correctly"
            "Present the findings clearly. If anti-patterns are found, list them and their suggestions. "
            "If no anti-patterns are found, state that. If there's an error using the tool, report the error."
        ),
        description=(
            "This agent analyzes BigQuery SQL queries for anti-patterns using a specialized tool "
            "that calls a local analysis service. It helps users identify potential issues in their queries."
        ),
        tools=[analyze_bigquery_sql_anti_patterns], # Pass the function directly
        # enable_tool_search=False # Consider this if you only have one tool and want to ensure it's always considered
    )