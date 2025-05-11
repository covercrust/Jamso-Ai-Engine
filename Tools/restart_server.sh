#!/bin/bash
echo "Server restart triggered at $(date)"
sleep 2
cd /home/jamso-ai-server/Jamso-Ai-Engine
bash run_local.sh

