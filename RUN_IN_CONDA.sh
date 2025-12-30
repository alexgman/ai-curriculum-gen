#!/bin/bash
# Run the backend in conda environment

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate curriculum

# Navigate to backend
cd /home/ubuntu/Dev/ai-curriculum-gen/backend

# Start the server
echo "🚀 Starting AI Curriculum Builder Backend in conda env..."
python -m app.main



