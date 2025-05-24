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
echo "7) Market Intelligence Tools"
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
        echo "3) Market Intelligence tests"
        echo "4) All tests"
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
                echo "Running market intelligence tests..."
                python Tests/Integration/test_market_intelligence.py
                ;;
            4)
                echo "Running all tests..."
                python -m pytest Tests/
                ;;
            *)
                echo "Invalid choice"
                ;;
        esac
        ;;
    7)
        echo "Market Intelligence Tools:"
        echo "1) Generate Daily Market Report"
        echo "2) Fetch Latest Market News"
        echo "3) Analyze Market Sentiment"
        echo "4) Monitor Market in Real-time"
        read -p "Enter choice: " mi_choice
        case $mi_choice in
            1)
                echo "Generating daily market report..."
                read -p "Enter symbols (comma-separated) or leave empty for defaults: " symbols
                read -p "Output format (html/json/csv) [default: html]: " format
                format=${format:-html}
                
                if [ -n "$symbols" ]; then
                    python Tools/market_intel.py report --symbols="$symbols" --format="$format"
                else
                    python Tools/market_intel.py report --format="$format"
                fi
                ;;
            2)
                echo "Fetching market news..."
                read -p "How many news items? [default: 10]: " count
                count=${count:-10}
                read -p "Category (general/forex/crypto/merger) [default: general]: " category
                category=${category:-general}
                
                python Tools/market_intel.py news --count="$count" --category="$category" --verbose
                ;;
            3)
                echo "Analyzing market sentiment..."
                read -p "Enter symbols (comma-separated) or leave empty for general market: " symbols
                read -p "How many days to look back? [default: 7]: " days
                days=${days:-7}
                
                if [ -n "$symbols" ]; then
                    python Tools/market_intel.py sentiment --symbols="$symbols" --days="$days" --verbose
                else
                    python Tools/market_intel.py sentiment --days="$days" --verbose
                fi
                ;;
            4)
                echo "Starting market monitor..."
                read -p "Enter symbols to monitor (comma-separated) or leave empty for defaults: " symbols
                read -p "Update interval in seconds [default: 60]: " interval
                interval=${interval:-60}
                
                if [ -n "$symbols" ]; then
                    python Tools/market_intel.py monitor --symbols="$symbols" --interval="$interval"
                else
                    python Tools/market_intel.py monitor --interval="$interval"
                fi
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
