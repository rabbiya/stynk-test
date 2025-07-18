"""
Chart Generator Agent
Creates interactive charts using Plotly based on BigQuery results
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from app.core.state import State

class ChartGenerator:
    """Generates interactive charts from BigQuery results"""
    
    def __init__(self):
        pass
    
    def generate_chart(self, state: State) -> State:
        """Generate chart based on results and chart type"""
        
        # Skip if no visualization needed or no results
        if not state.get("needs_visualization", False) or not state.get("result"):
            state["visualization_html"] = None
            state["chart_data"] = None
            return state
        
        chart_type = state.get("chart_type")
        if not chart_type:
            state["visualization_html"] = None
            state["chart_data"] = None
            return state
        
        try:
            # Convert results to DataFrame
            df = self._results_to_dataframe(state["result"])
            
            if df.empty:
                state["visualization_html"] = None
                state["chart_data"] = None
                return state
            
            # Generate chart data (JSON format - much smaller)
            chart_data = self._create_chart_data(df, chart_type, state["question"])
            state["chart_data"] = chart_data
            
            # Generate HTML chart (optional - can be disabled for large responses)
            try:
                if chart_type == "pie":
                    html = self._create_pie_chart(df, state["question"])
                elif chart_type == "bar":
                    html = self._create_bar_chart(df, state["question"])
                elif chart_type == "line":
                    html = self._create_line_chart(df, state["question"])
                elif chart_type == "histogram":
                    html = self._create_histogram(df, state["question"])
                else:
                    # Default to bar chart
                    html = self._create_bar_chart(df, state["question"])
                
                state["visualization_html"] = html
            except Exception as e:
                # If HTML generation fails, continue with just the data
                state["visualization_html"] = None
                print(f"HTML chart generation failed: {e}")
            
        except Exception as e:
            # If chart generation fails, continue without visualization
            state["visualization_html"] = None
            state["chart_data"] = None
            print(f"Chart generation failed: {e}")
        
        return state
    
    def _results_to_dataframe(self, results):
        """Convert BigQuery results to pandas DataFrame"""
        if not results or len(results) < 2:
            return pd.DataFrame()
        
        # First row contains column headers
        headers = results[0]
        data = results[1:]
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Try to convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        
        # Clean up data - handle string arrays and empty values
        for col in df.columns:
            if df[col].dtype == 'object':
                # Clean up string arrays like "['Horror']" or "['Comedy', 'Drama']"
                df[col] = df[col].astype(str).apply(self._clean_string_array)
        
        return df
    
    def _clean_string_array(self, value):
        """Clean string array values for better display"""
        if not value or value == "nan":
            return "Unknown"
        
        # Handle string arrays like "['Horror']" or "['Comedy', 'Drama']"
        if value.startswith('[') and value.endswith(']'):
            # Extract the content between brackets
            content = value[1:-1]
            # Split by comma and clean up quotes and spaces
            items = [item.strip().strip("'\"") for item in content.split(',')]
            # Join multiple genres with " & "
            return " & ".join(items) if items else "Unknown"
        
        return value
    
    def _create_pie_chart(self, df, question):
        """Create a pie chart"""
        if len(df.columns) < 2:
            return None
        
        # Use first two columns: labels and values
        labels_col = df.columns[0]
        values_col = df.columns[1]
        
        # Ensure values are numeric
        df[values_col] = pd.to_numeric(df[values_col], errors='coerce')
        df = df.dropna(subset=[values_col])
        
        if df.empty:
            return None
        
        fig = go.Figure(data=[go.Pie(
            labels=df[labels_col].astype(str),
            values=df[values_col],
            hole=0.3,
            textinfo='label+percent',
            textposition='inside'
        )])
        
        fig.update_layout(
            title=f"Pie Chart: {question}",
            height=500,
            showlegend=True,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Use CDN version instead of embedding full library
        return fig.to_html(
            include_plotlyjs='cdn',  # Use CDN instead of embedding
            full_html=False,
            config={'displayModeBar': False}  # Remove the mode bar to reduce size
        )
    
    def _create_bar_chart(self, df, question):
        """Create a bar chart"""
        if len(df.columns) < 2:
            return None
        
        # Use first two columns: categories and values
        x_col = df.columns[0]
        y_col = df.columns[1]
        
        # Ensure values are numeric
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        df = df.dropna(subset=[y_col])
        
        if df.empty:
            return None
        
        fig = go.Figure(data=[go.Bar(
            x=df[x_col].astype(str),
            y=df[y_col],
            text=df[y_col],
            textposition='auto',
        )])
        
        fig.update_layout(
            title=f"Bar Chart: {question}",
            xaxis_title=x_col,
            yaxis_title=y_col,
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Use CDN version instead of embedding full library
        return fig.to_html(
            include_plotlyjs='cdn',  # Use CDN instead of embedding
            full_html=False,
            config={'displayModeBar': False}  # Remove the mode bar to reduce size
        )
    
    def _create_line_chart(self, df, question):
        """Create a line chart"""
        if len(df.columns) < 2:
            return None
        
        # Use first two columns: x-axis and y-axis
        x_col = df.columns[0]
        y_col = df.columns[1]
        
        # Ensure values are numeric
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        df = df.dropna(subset=[y_col])
        
        if df.empty:
            return None
        
        fig = go.Figure(data=[go.Scatter(
            x=df[x_col].astype(str),
            y=df[y_col],
            mode='lines+markers',
            line=dict(width=3),
            marker=dict(size=8)
        )])
        
        fig.update_layout(
            title=f"Line Chart: {question}",
            xaxis_title=x_col,
            yaxis_title=y_col,
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Use CDN version instead of embedding full library
        return fig.to_html(
            include_plotlyjs='cdn',  # Use CDN instead of embedding
            full_html=False,
            config={'displayModeBar': False}  # Remove the mode bar to reduce size
        )
    
    def _create_histogram(self, df, question):
        """Create a histogram"""
        if len(df.columns) < 1:
            return None
        
        # Use first column for histogram
        values_col = df.columns[0]
        
        # Ensure values are numeric
        df[values_col] = pd.to_numeric(df[values_col], errors='coerce')
        df = df.dropna(subset=[values_col])
        
        if df.empty:
            return None
        
        fig = go.Figure(data=[go.Histogram(
            x=df[values_col],
            nbinsx=20,
            opacity=0.7
        )])
        
        fig.update_layout(
            title=f"Histogram: {question}",
            xaxis_title=values_col,
            yaxis_title="Frequency",
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Use CDN version instead of embedding full library
        return fig.to_html(
            include_plotlyjs='cdn',  # Use CDN instead of embedding
            full_html=False,
            config={'displayModeBar': False}  # Remove the mode bar to reduce size
        )

    def _create_chart_data(self, df, chart_type, question):
        """Create chart data in JSON format (much smaller than HTML)"""
        if len(df.columns) < 2:
            return None
        
        # Prepare data for the chart
        if chart_type == "pie":
            labels_col = df.columns[0]
            values_col = df.columns[1]
            
            # Ensure values are numeric
            df[values_col] = pd.to_numeric(df[values_col], errors='coerce')
            df = df.dropna(subset=[values_col])
            
            if df.empty:
                return None
            
            return {
                "type": "pie",
                "data": {
                    "labels": df[labels_col].astype(str).tolist(),
                    "values": df[values_col].tolist()
                },
                "title": f"Pie Chart: {question}",
                "config": {
                    "hole": 0.3,
                    "textinfo": "label+percent",
                    "textposition": "inside"
                }
            }
        
        elif chart_type in ["bar", "line"]:
            x_col = df.columns[0]
            y_col = df.columns[1]
            
            # Ensure values are numeric
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
            df = df.dropna(subset=[y_col])
            
            if df.empty:
                return None
            
            return {
                "type": chart_type,
                "data": {
                    "x": df[x_col].astype(str).tolist(),
                    "y": df[y_col].tolist()
                },
                "title": f"{chart_type.title()} Chart: {question}",
                "config": {
                    "xaxis_title": x_col,
                    "yaxis_title": y_col
                }
            }
        
        elif chart_type == "histogram":
            values_col = df.columns[0]
            
            # Ensure values are numeric
            df[values_col] = pd.to_numeric(df[values_col], errors='coerce')
            df = df.dropna(subset=[values_col])
            
            if df.empty:
                return None
            
            return {
                "type": "histogram",
                "data": {
                    "values": df[values_col].tolist()
                },
                "title": f"Histogram: {question}",
                "config": {
                    "xaxis_title": values_col,
                    "yaxis_title": "Frequency",
                    "nbinsx": 20
                }
            }
        
        return None

def generate_chart(state: State) -> State:
    """Entry point for chart generation"""
    generator = ChartGenerator()
    return generator.generate_chart(state) 