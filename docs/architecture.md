# Architecture Overview 🏗️

## System Components

The BigQuery SQL Agent is built with a modular architecture that processes natural language questions through a series of specialized AI agents.

```mermaid
graph TD
    A["User Question"] --> B["Intent Detector"]
    B --> C{Intent Type}
    C -->|"sql_query"| D["Query Generator"]
    C -->|"greeting"| E["Friendly Response"]
    C -->|"out_of_scope"| F["Scope Guidance"]
    D --> G["Query Executor"]
    G --> H["Answer Generator"]
    H --> I["Final Response"]
    
    J["BigQuery Connection"] --> D
    J --> G
    K["LangSmith Tracing"] --> B
    K --> D
    K --> G
    K --> H
    L["Session Memory"] --> B
    L --> H

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#bbf,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
    style J fill:#bfb,stroke:#333,stroke-width:2px
    style K fill:#fbf,stroke:#333,stroke-width:2px
    style L fill:#fbb,stroke:#333,stroke-width:2px
```

## Component Details

### 1. Intent Detector
- Uses GPT-4 to classify user questions
- Handles greetings, SQL queries, and out-of-scope requests
- Maintains conversation context

### 2. Query Generator
- Converts natural language to BigQuery SQL
- Applies safety limits and best practices
- Handles schema information

### 3. Query Executor
- Runs SQL with safety limits
- Manages BigQuery connection
- Handles errors gracefully

### 4. Answer Generator
- Creates natural language insights
- Formats results for display
- Maintains conversation history

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant LangGraph
    participant Intent as Intent Detector
    participant Query as Query Generator  
    participant Executor as Query Executor
    participant Answer as Answer Generator
    participant BigQuery
    
    User->>FastAPI: POST /ask
    FastAPI->>LangGraph: create_initial_state()
    LangGraph->>Intent: detect_intent()
    Intent->>Intent: GPT-4 classification
    Intent-->>LangGraph: intent="sql_query"
    
    LangGraph->>Query: generate_query()
    Query->>BigQuery: get schema info
    BigQuery-->>Query: table schemas
    Query->>Query: GPT-4 SQL generation
    Query-->>LangGraph: SQL query
    
    LangGraph->>Executor: execute_query()
    Executor->>BigQuery: run SQL with limits
    BigQuery-->>Executor: query results
    Executor-->>LangGraph: formatted data
    
    LangGraph->>Answer: generate_answer()
    Answer->>Answer: GPT-4 insight generation
    Answer-->>LangGraph: final insights
    
    LangGraph-->>FastAPI: complete state
    FastAPI-->>User: JSON response
```

## Directory Structure

```
app/
├── agents/          # AI processing agents
│   ├── intent_detector.py    # Classify user intent
│   ├── query_generator.py    # Generate BigQuery SQL
│   ├── query_executor.py     # Execute queries safely
│   └── answer_generator.py   # Create natural responses
├── core/           # System core
│   ├── state.py    # State management
│   └── graph.py    # LangGraph workflow
├── db/             # Database layer
│   └── connection.py # BigQuery connection
├── models.py       # API models
└── main.py         # FastAPI app
```

## Technology Stack

- **FastAPI**: Web framework
- **LangGraph**: Workflow orchestration
- **OpenAI GPT-4**: Language model
- **BigQuery**: Database
- **LangSmith**: Tracing and monitoring
- **tiktoken**: Token counting

## Memory Management

```mermaid
graph LR
    A[User Question] --> B[Session Memory]
    B --> C[Conversation History]
    C --> D[Last 5 Interactions]
    D --> E[Token Usage]
    E --> F[Query Results]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:2px
    style D fill:#fbf,stroke:#333,stroke-width:2px
    style E fill:#fbb,stroke:#333,stroke-width:2px
    style F fill:#bff,stroke:#333,stroke-width:2px
``` 