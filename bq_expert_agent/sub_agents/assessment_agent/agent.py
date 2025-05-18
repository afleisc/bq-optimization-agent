from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.toolbox_tool import ToolboxTool

toolbox = ToolboxTool("http://127.0.0.1:5000")

assessment_agent = LlmAgent(
    name="assessment_agent", 
    model="gemini-2.0-flash",
    tools=toolbox.get_toolset(toolset_name='bq-assessment-toolset'),
    description="I use BigQuery metadata provided by the extraction agent to analyze information schema information and provide expert assessment of current state"
    )
