"""
Main entry point for the EV Charger Deployment Analysis tool.

This application provides a comprehensive analysis of regulated asset base (RAB)
approaches to electric vehicle charging infrastructure deployment.
"""

from src.visualisation.dashboard import render_dashboard

if __name__ == "__main__":
    render_dashboard() 