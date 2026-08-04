#!/usr/bin/env python3
from run_data_refresh import current_status, atomic_json, LATEST
import json

status = current_status()
atomic_json(LATEST, status)
print(json.dumps(status, indent=2))
