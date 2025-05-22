from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import SequentialAgent

optimization_agent = LlmAgent(
      model='gemini-2.5-pro-preview-03-25', 
      name='bigquery_optimization_assistant',
      instruction='''
      You are an expert google cloud data warehouse engineer. 
      The assessment agent has provided you with a query text and corresponding antipatterns.
      Rewrite the SQL text given the provided antipatterns and return it to the user.''',
)
  