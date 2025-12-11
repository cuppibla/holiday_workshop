#!/bin/bash

# Script to deploy the agent and update the .env file with the new Agent Engine ID
# Usage: ./deploy_and_update_env.sh

# Navigate to the script's directory to ensure relative paths work
cd "$(dirname "$0")"

# Define paths
WORKSPACE_ROOT="../.."
ENV_FILE="$WORKSPACE_ROOT/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "Loading environment variables from $ENV_FILE..."
# Export variables so the python script can pick them up easily
set -a
source "$ENV_FILE"
set +a

echo "------------------------------------------------"
echo "Starting Agent Deployment..."
echo "------------------------------------------------"

# Run the deployment script and capture both stdout and stderr (but we only process stdout for ID)
# We use a temporary file to store output to process it and show it to the user
OUTPUT_FILE=$(mktemp)

# Change to backend directory and run using uv, ensuring we return to previous directory
pushd backend > /dev/null
uv run python deploy_agent.py 2>&1 | tee "$OUTPUT_FILE"
EXIT_CODE=${PIPESTATUS[0]}
popd > /dev/null

if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: Deployment failed."
    rm "$OUTPUT_FILE"
    exit $EXIT_CODE
fi

# Extract Agent Engine ID
# Looking for line: "Agent Engine ID: <id>"
AGENT_ID=$(grep "Agent Engine ID:" "$OUTPUT_FILE" | awk -F': ' '{print $2}' | tr -d '[:space:]')

rm "$OUTPUT_FILE"

if [ -z "$AGENT_ID" ]; then
    echo "Error: Could not extract Agent Engine ID from deployment output."
    exit 1
fi

echo "------------------------------------------------"
echo "Deployment Successful!"
echo "Captured Agent Engine ID: $AGENT_ID"
echo "------------------------------------------------"

# Update .env file safely using a small Python script
python3 -c "
import sys
import re

env_path = '$ENV_FILE'
new_id = '$AGENT_ID'

try:
    with open(env_path, 'r') as f:
        content = f.read()

    # 1. Update AGENT_ENGINE_ID
    # Matches 'export AGENT_ENGINE_ID=...' and replaces the value
    # 1. Update AGENT_ENGINE_ID
    # Matches 'export AGENT_ENGINE_ID=...' or 'AGENT_ENGINE_ID=...' and replaces the value
    if re.search(r'(?:export\s+)?AGENT_ENGINE_ID=', content):
        content = re.sub(r'(?:export\s+)?AGENT_ENGINE_ID=.*', f'AGENT_ENGINE_ID={new_id}', content)
        print(f'Updated AGENT_ENGINE_ID to {new_id}')
    else:
        # Append if not found
        content += f'\nAGENT_ENGINE_ID={new_id}\n'
        print(f'Added AGENT_ENGINE_ID={new_id}')

    # 2. Update USE_MEMORY_BANK
    # Matches 'export USE_MEMORY_BANK=false' or 'USE_MEMORY_BANK=false'
    # We want to set it to TRUE (uppercase) as requested
    if re.search(r'(?:export\s+)?USE_MEMORY_BANK=false', content):
        content = re.sub(r'(?:export\s+)?USE_MEMORY_BANK=false', 'USE_MEMORY_BANK=TRUE', content)
        print('Updated USE_MEMORY_BANK to TRUE')
    elif re.search(r'(?:export\s+)?USE_MEMORY_BANK=(?:true|TRUE)', content, re.IGNORECASE):
        # normalize to TRUE if it exists but is lowercase/mixed or just leave it? 
        # User asked for TRUE. Let's force it to TRUE if it's already true-ish but not TRUE?
        # Actually simplest is just to check if it's already true-ish.
        print('USE_MEMORY_BANK is already true/TRUE')
    else:
        # If the variable isn't there or is weird, strictly following instructions to change false to true.
        # If it's incomplete, we might append it.
        pass

    with open(env_path, 'w') as f:
        f.write(content)

    print(f'Successfully updated {env_path}')

except Exception as e:
    print(f'Error updating .env: {e}')
    sys.exit(1)
"
