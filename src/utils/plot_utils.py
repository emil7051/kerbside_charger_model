"""
Utility functions for creating consistent plots across the application.
"""

import plotly.express as px
import plotly.graph_objects as go

def create_line_chart(df, x_col, y_col, title, y_label=None, markers=True):
    """
    Create a line chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column or index for x-axis
        y_col (str or list): Column(s) for y-axis
        title (str): Chart title
        y_label (str, optional): Custom y-axis label
        markers (bool): Whether to show markers
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if y_label is None:
        y_label = y_col if isinstance(y_col, str) else "Value"
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        labels={y_col: y_label, "index": "Year"},
        markers=markers
    )
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title=y_label),
        hovermode="x unified"
    )
    
    return fig

def create_stacked_area_chart(df, x_col, y_cols, title, labels=None, y_label="Value"):
    """
    Create a stacked area chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column or index for x-axis
        y_cols (list): List of columns for y-axis
        title (str): Chart title
        labels (dict, optional): Dictionary mapping column names to display names
        y_label (str): Y-axis label
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if labels is None:
        labels = {}
    
    fig = go.Figure()
    
    for component in y_cols:
        fig.add_trace(
            go.Scatter(
                x=df[x_col] if x_col in df.columns else df.index,
                y=df[component],
                name=labels.get(component, component),
                stackgroup="one"
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title=y_label),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_bar_chart(df, x_col, y_col, title, color=None, y_label=None):
    """
    Create a bar chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column for x-axis
        y_col: Column for y-axis
        title (str): Chart title
        color (str, optional): Column to use for bar colors
        y_label (str, optional): Custom y-axis label
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if y_label is None:
        y_label = y_col
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color,
        title=title,
        labels={y_col: y_label, x_col: x_col}
    )
    
    fig.update_layout(
        yaxis=dict(title=y_label),
        hovermode="closest"
    )
    
    return fig 