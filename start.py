#!/usr/bin/env python3
"""Startup script for Railway deployment"""
import os
import sys

if __name__ == "__main__":
    port = os.environ.get("PORT", "8000")
    
    # Import and run uvicorn programmatically
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=int(port),
        log_level="info"
    )
