#!/usr/bin/env bash
endpoint="http://172.27.0.1:8000/multi_agent_chat/"
session_id=$(uuidgen)
declare -a msgs=(
  "I want to know my credit card balance."
  "account number is A1234567890."
  "how to open dispuate PayPal Account"
  "last transaction."
  "Was ist meine letzte Transaktion?."
)

for msg in "${msgs[@]}"; do
  printf '\n=== %s ===\n' "$msg"
  curl -sS -N \
    -H "Content-Type: application/json" \
    -d "{\"user_message\":\"$msg\",\"conversation_id\":\"$session_id\"}" \
    -w '\n-- elapsed: %{time_total}s --\n' \
    "$endpoint"
done
