#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting BQ Optimization Agent Setup..."

# --- Download yq (needed early for tools.yaml processing) ---
# Check https://github.com/mikefarah/yq/releases for the latest version
YQ_VERSION="v4.44.1"
YQ_EXECUTABLE="./yq"

if [ -f "$YQ_EXECUTABLE" ]; then
    echo "ℹ️ yq executable already exists. Skipping download."
else
    echo "📥 Downloading yq version $YQ_VERSION..."
    # Determine OS and architecture for correct download URL
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)

    case "$OS" in
        linux)
            case "$ARCH" in
                x86_64) YQ_URL="https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_linux_amd64" ;;
                arm64) YQ_URL="https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_linux_arm64" ;;
                *) echo "❌ Unsupported architecture for yq: $ARCH on $OS" && exit 1 ;;
            esac
            ;;
        darwin) # macOS
            case "$ARCH" in
                x86_64) YQ_URL="https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_darwin_amd64" ;;
                arm64) YQ_URL="https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_darwin_arm64" ;;
                *) echo "❌ Unsupported architecture for yq: $ARCH on $OS" && exit 1 ;;
            esac
            ;;
        *) echo "❌ Unsupported OS for yq: $OS" && exit 1 ;;
    esac

    curl -sL "$YQ_URL" -o "$YQ_EXECUTABLE"
    chmod +x "$YQ_EXECUTABLE"
    echo "✅ yq downloaded and made executable."
fi

# --- Configuration for .env ---
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

# --- Configure tools.yaml project and location ---
TOOLS_YAML="tools.yaml"
BQ_SOURCE_PATH='.sources."my-bigquery-source"'
BQ_PROJECT_PATH="${BQ_SOURCE_PATH}.project"
BQ_LOCATION_PATH="${BQ_SOURCE_PATH}.location"

# Use the downloaded yq executable
YQ="$YQ_EXECUTABLE"

# Ensure tools.yaml exists before trying to read/write to it
if [ ! -f "$TOOLS_YAML" ]; then
    echo "⚠️ $TOOLS_YAML not found. A basic structure will be created."
    cat <<EOL > "$TOOLS_YAML"
sources:
  my-bigquery-source:
    kind: bigquery
    project:
    location:
EOL
fi

echo "🔍 Checking and configuring $TOOLS_YAML..."

TOOLS_YAML_PROJECT=$("$YQ" e "$BQ_PROJECT_PATH" "$TOOLS_YAML" || true) # Use || true to prevent exit on error if path doesn't exist
TOOLS_YAML_LOCATION=$("$YQ" e "$BQ_LOCATION_PATH" "$TOOLS_YAML" || true)

# Check if project is set in tools.yaml
if [ -z "$TOOLS_YAML_PROJECT" ] || [ "$TOOLS_YAML_PROJECT" == "null" ]; then
    echo "⚠️ BigQuery project is not set in $TOOLS_YAML."
    read -p "Enter the Google Cloud Project ID for BigQuery source (default: ${GOOGLE_CLOUD_PROJECT}): " NEW_PROJECT_ID
    NEW_PROJECT_ID=${NEW_PROJECT_ID:-$GOOGLE_CLOUD_PROJECT} # Use default if empty
    "$YQ" -i e "${BQ_PROJECT_PATH} = \"${NEW_PROJECT_ID}\"" "$TOOLS_YAML"
    echo "✅ Project ID set to '${NEW_PROJECT_ID}' in $TOOLS_YAML."
    TOOLS_YAML_PROJECT="$NEW_PROJECT_ID" # Update the variable for later use
else
    echo "✅ BigQuery Project '$TOOLS_YAML_PROJECT' found in $TOOLS_YAML."
fi

# Check if location is set in tools.yaml
if [ -z "$TOOLS_YAML_LOCATION" ] || [ "$TOOLS_YAML_LOCATION" == "null" ]; then
    echo "⚠️ BigQuery location is not set in $TOOLS_YAML."
    read -p "Enter the Google Cloud Location for BigQuery source (default: ${GOOGLE_CLOUD_LOCATION}): " NEW_LOCATION_ID
    NEW_LOCATION_ID=${NEW_LOCATION_ID:-$GOOGLE_CLOUD_LOCATION} # Use default if empty
    "$YQ" -i e "${BQ_LOCATION_PATH} = \"${NEW_LOCATION_ID}\"" "$TOOLS_YAML"
    echo "✅ Location set to '${NEW_LOCATION_ID}' in $TOOLS_YAML."
    TOOLS_YAML_LOCATION="$NEW_LOCATION_ID" # Update the variable for later use
else
    echo "✅ BigQuery Location '$TOOLS_YAML_LOCATION' found in $TOOLS_YAML."
fi

# --- Python Environment and Tool Setup ---

echo "📦 Setting up Python environment with uv..."
# Create a virtual environment using uv (if you prefer a local .venv folder, uncomment the next line)
# uv venv .venv
# source .venv/bin/activate # Uncomment if you created a local .venv

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
    curl -sL https://storage.googleapis.com/genai-toolbox/v$TOOLBOX_VERSION/linux/amd64/toolbox -o "$TOOLBOX_EXECUTABLE"
    chmod +x "$TOOLBOX_EXECUTABLE"
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

# --- Setup Complete! ---

echo "🎉 Setup Complete!"
echo ""
echo "👉 Next Steps (Run these in separate terminals):"
echo "    1. Terminal 1 (Toolbox): ./toolbox --tools-file \"tools.yaml\""
echo "    2. Terminal 2 (Antipattern Tool): cd bigquery-antipattern-recognition && mvn org.springframework.boot:spring-boot-maven-plugin:run"
echo "    3. Terminal 3 (ADK): adk web"
echo ""
echo "Ensure you have sourced your environment variables if needed: source .env"
echo "And if you created a uv virtual environment, activate it: source .venv/bin/activate (or your chosen path)"