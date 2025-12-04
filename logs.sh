#!/bin/bash

# QuantAgent Logs Script

echo "📋 QuantAgent Logs (press Ctrl+C to exit)"
echo "=========================================="
echo ""

docker-compose logs -f quantagent
