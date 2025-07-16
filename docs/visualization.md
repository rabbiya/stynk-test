# Visualization Features

This document describes the visualization capabilities added to the BigQuery SQL Agent chatbot.

## Overview

The chatbot now supports automatic generation of interactive charts and graphs when users request visualizations. The system can detect visualization requests and generate appropriate chart types using Plotly.

## Features

### 1. Automatic Visualization Detection

The system automatically detects when a user query requires visualization based on keywords such as:
- `chart`, `graph`, `plot`, `visualize`, `visualization`
- `show me`, `display`, `see`, `view`
- `pie chart`, `bar chart`, `line chart`, `histogram`
- `trend`, `comparison`, `distribution`, `breakdown`
- `percentage`, `proportion`, `ratio`
- `top`, `bottom`, `ranking`, `list`
- `over time`, `by month`, `by year`, `by region`

### 2. Supported Chart Types

The system supports four main chart types:

#### Pie Charts
- **Use Case**: Percentages, proportions, parts of a whole
- **Example Queries**: 
  - "Show me a pie chart of movie genres"
  - "What's the distribution of content types?"

#### Bar Charts
- **Use Case**: Comparisons, rankings, categories
- **Example Queries**:
  - "What are the top 5 movies by views?"
  - "Compare cinema chains by attendance"

#### Line Charts
- **Use Case**: Trends over time, time series data
- **Example Queries**:
  - "Show trends over time for movie releases"
  - "Monthly viewership trends"

#### Histograms
- **Use Case**: Distributions, frequency data
- **Example Queries**:
  - "Distribution of movie ratings"
  - "Frequency of showtimes by hour"

### 3. Dynamic Chart Generation

Charts are generated dynamically based on:
- **Query Results**: Automatically uses the first two columns for x/y axes
- **Data Types**: Automatically converts numeric data for proper visualization
- **Chart Type**: Selects appropriate visualization based on the query context

### 4. Lightweight Response Format

To optimize API response size, the system provides two visualization formats:

#### Chart Data (Recommended)
- **Format**: JSON data structure
- **Size**: ~1-5KB (vs 2MB+ for embedded HTML)
- **Usage**: Client-side rendering with Plotly CDN
- **Benefits**: Fast API responses, flexible rendering

#### Chart HTML (Optional)
- **Format**: Complete HTML with embedded Plotly
- **Size**: ~2MB+ (includes full Plotly library)
- **Usage**: Direct embedding in web pages
- **Benefits**: Self-contained, no external dependencies

## Architecture

### Workflow Integration

The visualization features are integrated into the existing LangGraph workflow:

```
Intent Detection → Visualization Detection → Query Generation → Query Execution → Chart Generation → Answer Generation
```

### New Components

1. **Visualization Detector** (`app/agents/visualization_detector.py`)
   - Analyzes user queries for visualization keywords
   - Determines appropriate chart type
   - Uses LLM for intelligent chart type selection

2. **Chart Generator** (`app/agents/chart_generator.py`)
   - Converts BigQuery results to pandas DataFrames
   - Generates lightweight JSON chart data
   - Optionally generates HTML charts
   - Handles different chart types dynamically

3. **Updated State Management** (`app/core/state.py`)
   - Added visualization-related fields
   - Tracks chart type and generated data

4. **Enhanced API Response** (`app/models.py`)
   - Includes visualization metadata
   - Returns both chart data and optional HTML

## API Response Format

The API response now includes visualization fields:

```json
{
  "query": "SELECT genre, COUNT(*) FROM movies GROUP BY genre",
  "result": [["genre", "count"], ["Action", 150], ["Drama", 200]],
  "insights": "The data shows that Drama is the most popular genre...",
  "needs_visualization": true,
  "chart_type": "pie",
  "chart_data": {
    "type": "pie",
    "data": {
      "labels": ["Action", "Drama"],
      "values": [150, 200]
    },
    "title": "Pie Chart: Show me a pie chart of movie genres",
    "config": {
      "hole": 0.3,
      "textinfo": "label+percent",
      "textposition": "inside"
    }
  },
  "visualization_html": "<div>...</div>",
  "token_usage": {...},
  "session_id": "user_session",
  "conversation_count": 1
}
```

## Usage Examples

### Example 1: Pie Chart Request
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me a pie chart of movie genres",
    "session_id": "test_session"
  }'
```

### Example 2: Bar Chart Request
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 5 movies by views? Create a bar chart",
    "session_id": "test_session"
  }'
```

### Example 3: Line Chart Request
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show trends over time for movie releases",
    "session_id": "test_session"
  }'
```

## Client-Side Rendering

### Using Chart Data (Recommended)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="chart"></div>
    <script>
        // Fetch data from API
        fetch('/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: "Show me a pie chart of genres"})
        })
        .then(response => response.json())
        .then(data => {
            if (data.chart_data) {
                const trace = {
                    type: data.chart_data.type,
                    labels: data.chart_data.data.labels,
                    values: data.chart_data.data.values
                };
                Plotly.newPlot('chart', [trace], {title: data.chart_data.title});
            }
        });
    </script>
</body>
</html>
```

### Using Chart HTML (Alternative)

```html
<div id="chart-container">
    <!-- The visualization_html field contains the complete chart -->
    ${data.visualization_html}
</div>
```

## Testing

### Test Script
Run the test script to verify visualization functionality:

```bash
python test_visualization.py
```

### HTML Viewers
- `visualization_viewer.html` - Shows both chart data and HTML
- `chart_renderer.html` - Lightweight viewer using chart data only

## Dependencies

The visualization features require these additional packages:
- `plotly`: For interactive chart generation
- `matplotlib`: For additional chart types (if needed)
- `pandas`: For data manipulation

## Configuration

No additional configuration is required. The visualization features work automatically with the existing BigQuery setup.

## Error Handling

- If chart generation fails, the system continues without visualization
- Invalid chart types default to bar charts
- Missing or invalid data gracefully handles errors
- Token usage is tracked for visualization detection

## Performance Considerations

### Response Size Optimization
- **Chart Data**: ~1-5KB per response
- **Chart HTML**: ~2MB+ per response (includes full Plotly library)
- **Recommendation**: Use chart_data for API responses, render client-side

### Processing Overhead
- Chart generation adds minimal overhead to the workflow
- Plotly charts are lightweight and responsive
- Token usage is minimal for visualization detection

## Future Enhancements

Potential improvements for future versions:
- Support for more chart types (scatter plots, heatmaps)
- Custom chart styling and themes
- Chart export functionality (PNG, PDF)
- Interactive chart customization options
- Multi-chart responses for complex queries
- Chart caching for repeated queries 