from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.toolbox_tool import ToolboxTool

toolbox = ToolboxTool("http://127.0.0.1:5000")

extraction_agent = LlmAgent(
    name="extraction_agent",
    model="gemini-2.0-flash",   
    instruction = "I extract the necessary metadata to optimize BigQuery by executing information schema queries. Wait for a response from the query before continuing.",
    tools=toolbox.get_toolset(toolset_name='bq-extraction-toolset'),
)
