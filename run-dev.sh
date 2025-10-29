#!/bin/bash

# Spotify Music Recommendation System - Development Runner
# This script starts both the backend and frontend in development mode

set -e

echo "🎵 Starting Spotify Music Recommendation System"
echo "============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file from .env.example and add your API keys."
    exit 1
fi

# Load environment variables safely (supports spaces, ignores invalid lines)
while IFS= read -r line || [ -n "$line" ]; do
    # Trim leading/trailing whitespace
    line="${line##*[![:space:]]}"
    line="${line%%*[![:space:]]}"

    # Skip comments and empty lines
    if [[ -z "$line" || "$line" =~ ^\s*# ]]; then
        continue
    fi

    # Require KEY=VALUE format
    if [[ "$line" != *"="* ]]; then
        echo "⚠ Skipping invalid .env line (expected KEY=VALUE): $line"
        continue
    fi

    key="${line%%=*}"
    value="${line#*=}"
    # Trim spaces around key
    key="${key//[[:space:]]/}"
    # Export as-is to preserve quotes in value if present
    export "$key=$value"
done < .env

# Ensure Python virtual environment exists and is activated
if [ ! -d .venv ]; then
	echo "🐍 Creating Python virtual environment at .venv ..."
	python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
. .venv/bin/activate
echo "✅ Activated virtual environment: $(python --version)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    exit 1
fi

echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip -q
if [ -f requirements.txt ]; then
	pip install -r requirements.txt -q
fi

echo ""
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt -q

echo ""
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install --silent

echo ""
echo "🚀 Starting services..."
echo ""

# Start backend in background
echo "▶️  Starting FastAPI backend on http://localhost:8000"
cd ../backend
python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend in background
echo "▶️  Starting React frontend on http://localhost:5173"
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📍 Backend API:  http://localhost:8000"
echo "📍 API Docs:     http://localhost:8000/docs"
echo "📍 Frontend:     http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap SIGINT and SIGTERM
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM

# Wait for processes
wait

