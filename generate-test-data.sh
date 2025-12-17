#!/bin/bash
# Generate fake test data with multiple customers, providers, and models
# Sends data directly to the collector API

COLLECTOR_URL="https://llmobserve-api-production-d791.up.railway.app"

PROVIDERS=("openai" "anthropic" "mistral" "cohere" "google")
MODELS_OPENAI=("gpt-4o" "gpt-4o-mini" "gpt-4-turbo" "gpt-3.5-turbo")
MODELS_ANTHROPIC=("claude-3-opus" "claude-3-sonnet" "claude-3-haiku" "claude-3.5-sonnet")
MODELS_MISTRAL=("mistral-large" "mistral-medium" "mistral-small")
MODELS_COHERE=("command-r+" "command-r")
MODELS_GOOGLE=("gemini-1.5-pro" "gemini-1.5-flash")

CUSTOMERS=("customer_acme_corp" "customer_techstart" "customer_enterprise_llc" "customer_startup_io" "customer_bigdata_inc")
FEATURES=("feature:chat_assistant" "feature:document_summary" "feature:code_review" "feature:email_composer" "feature:data_analysis")

# Get random element from array
random_choice() {
    local arr=("$@")
    echo "${arr[$RANDOM % ${#arr[@]}]}"
}

# Generate and send one event
send_event() {
    local hours_ago=$1
    
    # Random provider
    local provider=$(random_choice "${PROVIDERS[@]}")
    
    # Random model based on provider
    local model
    case $provider in
        "openai") model=$(random_choice "${MODELS_OPENAI[@]}") ;;
        "anthropic") model=$(random_choice "${MODELS_ANTHROPIC[@]}") ;;
        "mistral") model=$(random_choice "${MODELS_MISTRAL[@]}") ;;
        "cohere") model=$(random_choice "${MODELS_COHERE[@]}") ;;
        "google") model=$(random_choice "${MODELS_GOOGLE[@]}") ;;
    esac
    
    local customer=$(random_choice "${CUSTOMERS[@]}")
    local feature=$(random_choice "${FEATURES[@]}")
    
    local input_tokens=$((100 + RANDOM % 2000))
    local output_tokens=$((50 + RANDOM % 1000))
    local cost=$(echo "scale=6; ($input_tokens * 0.001 + $output_tokens * 0.002) / 1000" | bc)
    local latency=$((200 + RANDOM % 5000))
    
    local id="evt_${RANDOM}_$(date +%s%N)"
    local run_id="run_${RANDOM}_$(date +%s)"
    local span_id="span_${RANDOM}"
    
    curl -s -X POST "${COLLECTOR_URL}/events/" \
        -H "Content-Type: application/json" \
        -d "[{
            \"id\": \"${id}\",
            \"run_id\": \"${run_id}\",
            \"span_id\": \"${span_id}\",
            \"section\": \"${feature}\",
            \"span_type\": \"llm\",
            \"provider\": \"${provider}\",
            \"endpoint\": \"chat.completions\",
            \"model\": \"${model}\",
            \"input_tokens\": ${input_tokens},
            \"output_tokens\": ${output_tokens},
            \"cost_usd\": ${cost},
            \"latency_ms\": ${latency},
            \"status\": \"success\",
            \"customer_id\": \"${customer}\"
        }]" > /dev/null
}

echo "🚀 Generating fake test data..."
echo ""

# Generate events at different time points
# Recent data (last 24 hours)
echo "📊 Generating 30 events for the last few hours..."
for i in $(seq 1 30); do
    send_event 0
    printf "."
done
echo " ✅"

# Few hours ago
echo "📊 Generating 20 events from 2-6 hours ago..."
for i in $(seq 1 20); do
    send_event 4
    printf "."
done
echo " ✅"

# Yesterday
echo "📊 Generating 25 events from ~12-24 hours ago..."
for i in $(seq 1 25); do
    send_event 18
    printf "."
done
echo " ✅"

# 2-3 days ago
echo "📊 Generating 20 events from 2-3 days ago..."
for i in $(seq 1 20); do
    send_event 60
    printf "."
done
echo " ✅"

# 5-7 days ago
echo "📊 Generating 15 events from 5-7 days ago..."
for i in $(seq 1 15); do
    send_event 144
    printf "."
done
echo " ✅"

echo ""
echo "✨ Done! Generated 110 test events"
echo ""
echo "📈 Customers: ${CUSTOMERS[*]}"
echo "🔧 Features: ${FEATURES[*]}"
echo ""
echo "🔄 Refresh your dashboard to see the data!"

