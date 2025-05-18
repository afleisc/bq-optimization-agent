# BQ Optimization Agent

## Packages required
```
pip install toolbox-langchain langchain
pip install google-adk
```

## Setup ADK
`nano .env`

Paste the following and replace the variables with your own values:
```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=LOCATION
```

## Download toolbox
```
export VERSION=0.5.0

curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox

chmod +x toolbox
```

## Run the Agent

### Run the Toolbox
```
./toolbox --tools-file "tools.yaml"
```
open a new terminal

### Run the Antipattern tool
```
git clone https://github.com/afleisc/bigquery-antipattern-recognition.git
cd bigquery-antipattern-recognition
mvn org.springframework.boot:spring-boot-maven-plugin:run

```
open a new terminal

### Run the ADK
```
adk web
```

