"""Reusable Plotly chart builders for the dashboard."""
import plotly.express as px
import plotly.graph_objects as go


def bar_chart(df, x, y, title=None, color=None):
    fig = px.bar(df, x=x, y=y, title=title, color=color)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=350)
    return fig


def line_chart(df, x, y, title=None, color=None):
    fig = px.line(df, x=x, y=y, title=title, color=color, markers=True)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=350)
    return fig


def donut_chart(df, names, values, title=None):
    fig = px.pie(df, names=names, values=values, title=title, hole=0.5)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
    return fig


def bubble_chart(df, x, y, size, color, hover_name, title=None):
    fig = px.scatter(
        df, x=x, y=y, size=size, color=color, hover_name=hover_name,
        title=title, size_max=45,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=450)
    return fig


def radar_chart(categories, company_values, peer_avg_values, company_name, peer_group_name):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=company_values, theta=categories, fill="toself", name=company_name,
    ))
    fig.add_trace(go.Scatterpolar(
        r=peer_avg_values, theta=categories, fill="toself",
        name=f"{peer_group_name} avg", opacity=0.6,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True, margin=dict(l=20, r=20, t=30, b=20), height=450,
    )
    return fig


def sparkline(df, x, y, title=None):
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=220)
    return fig
