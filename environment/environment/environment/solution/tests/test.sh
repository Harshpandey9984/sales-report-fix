#!/bin/bash
# Verifier entrypoint. Harbor copies this folder to /tests and runs it after the agent finishes.
# It must write a numeric reward to /logs/verifier/reward.txt.

mkdir -p /logs/verifier
cd /app

python3 -m pytest /tests/test_outputs.py -v -p no:cacheprovider
status=$?

if [ $status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
exit $status
