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

"""Query Optimization Agent: Expert Agent to identify antipatterns and provide suggestions"""
import os
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
import google.auth

from .prompts import return_instructions_query_optimization

RUN_WITH_ADC = True


if RUN_WITH_ADC:

  application_default_credentials, _ = google.auth.default()

  credentials_config = BigQueryCredentialsConfig(

      credentials=application_default_credentials

  )

bigquery_toolset = BigQueryToolset(credentials_config=credentials_config)

query_agent = Agent(
    model=os.getenv("QUERY_AGENT_MODEL"),
    name="query_optimizer_agent",
    instruction=return_instructions_query_optimization(),
    tools=[bigquery_toolset],
)
