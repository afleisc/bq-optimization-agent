# BQ Optimization Agent

You need an existing Google Cloud account and a project.
1. Set up a Google Cloud project
2. Set up the gcloud CLI
3. Authenticate to Google Cloud, from the terminal by running `gcloud auth login`.
4. Enable the [Vertex AI API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com).

## Setup
1. `pip install uv`
2. `chmod +x setup_and_run.sh`
3. `./setup_and_run.sh`

It will prompt you for your GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION if the .env file doesn't exist.

👉 Next Steps (Run these in separate terminals):
   1. Terminal 1 (Toolbox): `./toolbox --tools-file \"tools.yaml\"`
   2. Terminal 2 (Antipattern Tool): `cd bigquery-antipattern-recognition && mvn org.springframework.boot:spring-boot-maven-plugin:run`
   3. Terminal 3 (ADK): `adk web`

