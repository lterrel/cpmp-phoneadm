#!/usr/bin/env zsh
#set -x 
# Login to API
# Interact with the token generate for the next operations
PBX="https://192.168.15.200:8088"
USER="api"
PASS="c72275af1021cf39fe0ef4027bd47394"

# Login
TOKEN=$(curl -k -s -X POST $PBX/api/v1.1.0/login \
  -H "Content-Type: application/json" \
  -d "{
        \"username\": \"$USER\",
        \"password\": \"$PASS\"
      }" | jq -r '.token')

echo "TOKEN=$TOKEN"

# Extension list (token en URL)
curl -k -s -X POST \
  "$PBX/api/v1.1.0/extensionlist/query?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq

# Query specific extension settings
curl -k -s -X POST \
  "$PBX/api/v1.1.0/extension/query?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
  	\"extid\": \"580\"
      }" | jq

# Modify name for specific extension
curl -k -s -X POST \
  "$PBX/api/v1.1.0/extension/update?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
  	\"extid\": \"580\",
	\"username\": \"Luis Terrel\"
      }" | jq
