#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting BQ Optimization Agent Setup..."

# --- Configuration ---
# Prompt for environment variables if not already set
if [ -f .env ]; then
    echo "ℹ️ .env file already exists. Skipping creation."
    source .env # Load existing .env variables to check them
else
    echo "📝 Creating .env file..."
    read -p "Enter your GOOGLE_CLOUD_PROJECT: " GOOGLE_CLOUD_PROJECT
    read -p "Enter your GOOGLE_CLOUD_LOCATION: " GOOGLE_CLOUD_LOCATION

    cat <<EOL > .env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}
EOL
    echo "✅ .env file created."
fi

# Ensure variables are set
if [ -z "${GOOGLE_CLOUD_PROJECT}" ] || [ -z "${GOOGLE_CLOUD_LOCATION}" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in the .env file."
    exit 1
fi

echo "📦 Setting up Python environment with uv..."
# Create a virtual environment using uv (if you want to explicitly create one, otherwise uv uses a global cache)
 uv venv .venv # Uncomment if you prefer a local .venv folder
 source .venv/bin/activate # Uncomment if you created a local .venv

# Install dependencies using uv
#uv pip install -r requirements.txt # If you generate a requirements.txt from pyproject.toml
# OR, if uv supports direct pyproject.toml installation well for your version (recommended):
uv pip sync pyproject.toml

echo "✅ Python dependencies installed."

# --- Download Toolbox ---
TOOLBOX_VERSION="0.5.0"
TOOLBOX_EXECUTABLE="./toolbox"

if [ -f "$TOOLBOX_EXECUTABLE" ]; then
    echo "ℹ️ Toolbox executable already exists. Skipping download."
else
    echo "📥 Downloading Toolbox version $TOOLBOX_VERSION..."
    curl -O https://storage.googleapis.com/genai-toolbox/v$TOOLBOX_VERSION/linux/amd64/toolbox
    chmod +x toolbox
    echo "✅ Toolbox downloaded and made executable."
fi

# --- Clone BigQuery Antipattern Recognition (if not already cloned) ---
ANTIPATTERN_DIR="bigquery-antipattern-recognition"
if [ -d "$ANTIPATTERN_DIR" ]; then
    echo "ℹ️ $ANTIPATTERN_DIR directory already exists. Assuming it's set up."
else
    echo "📥 Cloning BigQuery Antipattern Recognition tool..."
    git clone https://github.com/afleisc/bigquery-antipattern-recognition.git
    echo "✅ BigQuery Antipattern Recognition tool cloned."
fi

echo "🎉 Setup Complete!"
echo ""
echo "👉 Next Steps (Run these in separate terminals):"
echo "   1. Terminal 1 (Toolbox): ./toolbox --tools-file \"tools.yaml\""
echo "   2. Terminal 2 (Antipattern Tool): cd bigquery-antipattern-recognition && mvn org.springframework.boot:spring-boot-maven-plugin:run"
echo "   3. Terminal 3 (ADK): adk web"
echo ""
echo "Ensure you have sourced your environment variables if needed: source .env"
echo "And if you created a uv virtual environment, activate it: source .venv/bin/activate (or your chosen path)"