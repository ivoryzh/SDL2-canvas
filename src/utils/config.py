"""
Configuration settings for the SDL2 Canvas Integration.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SDL2 API Configuration
SDL2_API_BASE_URL = os.getenv("SDL2_API_BASE_URL", "http://localhost:8000")

# Task polling configuration
TASK_POLL_INTERVAL_SECONDS = int(os.getenv("TASK_POLL_INTERVAL_SECONDS", "5"))
TASK_MAX_WAIT_SECONDS = int(os.getenv("TASK_MAX_WAIT_SECONDS", "3600"))  # 1 hour default

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Canvas configuration
CANVAS_RESULT_FILE = os.getenv("CANVAS_RESULT_FILE", "result.json")
