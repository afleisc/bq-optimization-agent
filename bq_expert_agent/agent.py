from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.toolbox_tool import ToolboxTool
from .sub_agents.extraction_agent import extraction_agent
from .sub_agents.assessment_agent import assessment_agent
from .sub_agents.optimization_agent import optimization_agent
from google.adk.agents import SequentialAgent



toolbox = ToolboxTool("http://127.0.0.1:5000")

root_agent = LlmAgent(
      model='gemini-2.5-pro-preview-03-25', 
      name='bigquery_optimization_assistant',
      instruction='You are an expert google cloud data warehouse engineer. You have been urgently tasked with optimizing customers BigQuery environment.',
      sub_agents = [extraction_agent, assessment_agent, optimization_agent]
)
  