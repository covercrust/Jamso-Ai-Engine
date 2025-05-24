#!/bin/bash

# Jamso AI Engine - Startup Script
# This script provides a unified entry point to various launcher functions

echo "🚀 Jamso AI Engine - Startup Menu"
echo "================================="
echo ""
echo "Select an option:"
echo "1) Launch Main Application (jamso_launcher.py)"
echo "2) Start Local Development Server (run_local.sh)"
echo "3) Clean Python Cache Files (cleanup_cache.sh)"
echo "4) Run Health Check"
echo "5) Database Tools"
echo "6) Run Tests"
echo "q) Quit"
echo ""

read -p "Enter your choice: " choice

case $choice in
    1)
        echo "Starting main launcher..."
        python jamso_launcher.py
        ;;
    2)
        echo "Starting local development server..."
        ./run_local.sh
        ;;
    3)
        echo "Cleaning Python cache files..."
        ./cleanup_cache.sh
        ;;
    4)
        echo "Running health check..."
        bash Scripts/Maintenance/health_check.sh
        ;;
    5)
        echo "Database Tools:"
        echo "1) Check Sentiment Database Stats"
        echo "2) Debug Sentiment Database Issues"
        read -p "Enter choice: " db_choice
        case $db_choice in
            1)
                echo "Checking sentiment database statistics..."
                python Tools/Database/check_sentiment_db.py
                ;;
            2)
                echo "Debugging sentiment database issues..."
                python Tools/Database/debug_sentiment_db.py
                ;;
            *)
                echo "Invalid choice"
                ;;
        esac
        ;;
    6)
        echo "Select test type:"
        echo "1) Unit tests"
        echo "2) Integration tests"
        echo "3) All tests"
        read -p "Enter choice: " test_choice
        case $test_choice in
            1)
                echo "Running unit tests..."
                cd Tests/Unit && python -m pytest
                ;;
            2)
                echo "Running integration tests..."
                python Tests/Integration/test_integration.py --all
                ;;
            3)
                echo "Running all tests..."
                python -m pytest Tests/
                ;;
            *)
                echo "Invalid choice"
                ;;
        esac
        ;;
    q|Q)
        echo "Exiting"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
