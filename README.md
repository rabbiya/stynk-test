# BigQuery SQL Agent

A clean, modular SQL agent that converts natural language to BigQuery queries using LangGraph, LangSmith tracing, and tiktoken for monitoring.

## Features ✨

- **🧠 LangGraph Workflow** - Intelligent routing and memory management
- **📊 tiktoken Integration** - Precise token counting and cost monitoring  
- **🔍 LangSmith Tracing** - Full observability of LLM calls
- **💬 Conversation Memory** - Context-aware follow-up questions
- **🔒 Safe Execution** - Query validation and cost limits
- **☁️ BigQuery Native** - Optimized for BigQuery Standard SQL

## Quick Setup 🚀

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup BigQuery Service Account

**Get your service account JSON file:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **IAM & Admin > Service Accounts**
3. Create or select a service account with BigQuery permissions
4. Click **Keys > Add Key > Create New Key**
5. Choose **JSON format** and download
6. **Rename the file to `service_account.json`**
7. **Place it in the project root directory** (same folder as this README)

**Your project structure should look like:**
```
your-project/
├── app/
├── service_account.json  ← Place your JSON file here
├── run.py
├── README.md
└── .env
```

### 3. Configure Environment
```bash
cp .env.example .env
```

**Edit your `.env` file:**
```env
# Your BigQuery Configuration
BIGQUERY_PROJECT_ID=cogent-tine
BIGQUERY_DATASET=abc_data_mart

# Required OpenAI Configuration  
OPENAI_API_KEY=your-openai-api-key

# Optional - LangSmith for monitoring
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=bigquery-sql-agent
```

### 4. Run the Agent
```bash
python run.py
```

The script will verify your setup and start the API at `http://localhost:8000`

## Usage 📡

### Ask Questions About Your Data
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 5 products by sales?",
    "session_id": "user123"
  }'
```

### Example Questions You Can Ask
- "What are the total sales by region?"
- "Show me the top 10 customers by revenue"
- "What's the average order value this month?"
- "How many active users do we have?"

### Response Format
```json
{
  "query": "SELECT product_name, SUM(sales) as total_sales FROM `cogent-tine.abc_data_mart.sales` GROUP BY product_name ORDER BY total_sales DESC LIMIT 5",
  "result": [
    ["product_name", "total_sales"],
    ["Product A", 15000],
    ["Product B", 12000]
  ],
  "insights": "Based on the data, Product A has the highest sales...",
  "token_usage": {
    "total_tokens": 245,
    "intent_tokens": 65,
    "query_tokens": 120,
    "answer_tokens": 60
  },
  "session_id": "user123",
  "conversation_count": 1
}
```

## API Endpoints 🛡️

- `POST /ask` - Ask questions about your data
- `GET /conversation/{session_id}` - Get conversation history
- `GET /health` - Check system health and BigQuery connection
- `GET /` - Service status with dataset info

## Your BigQuery Setup 📊

- **Project:** `cogent-tine`
- **Dataset:** `abc_data_mart`
- **Full Reference:** `cogent-tine.abc_data_mart`

The agent will automatically:
- Connect to your specific project and dataset
- List available tables on startup
- Generate queries with proper table references
- Apply safety limits and validation

## Architecture 🏗️

```
app/
├── agents/           # AI processing agents
│   ├── intent_detector.py    # Classify user intent
│   ├── query_generator.py    # Generate BigQuery SQL
│   ├── query_executor.py     # Execute queries safely
│   └── answer_generator.py   # Create natural responses
├── core/             # System core
│   ├── state.py      # State management
│   └── graph.py      # LangGraph workflow
├── db/               # Database layer
│   └── connection.py # BigQuery connection
├── models.py         # API models
└── main.py          # FastAPI app
```

## Security & Safety 🔒

- Query validation (no DROP, DELETE, etc.)
- 1GB cost limit per query
- 30-second timeout
- Results limited to 100 rows
- Service account authentication
- Dataset-scoped access

## Monitoring 📈

With LangSmith enabled, you get:
- Real-time tracing of all LLM calls
- Token usage analytics
- Performance monitoring
- Error tracking and debugging

## Troubleshooting 🔧

**Common Issues:**

1. **"service_account.json not found"**
   - Make sure the file is in the project root (same folder as run.py)
   - Check the filename is exactly `service_account.json`

2. **"BigQuery connection failed"**
   - Verify your service account has BigQuery permissions
   - Check your project ID and dataset name in .env

3. **"No tables found"**
   - Confirm your dataset `abc_data_mart` exists in project `cogent-tine`
   - Verify your service account has access to the dataset

**For help:** Check the logs when running `python run.py` - they'll show exactly what's happening.

## License 📄

MIT License

---

**Built with:** FastAPI, LangGraph, LangChain, OpenAI GPT-4o, BigQuery, tiktoken
