# -*- coding: utf-8 -*-
"""Global settings for the multi-agent system."""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# Skills 目录
SKILLS_DIR = PROJECT_ROOT / "skills"

# 配置文件路径
AGENTS_CONFIG = PROJECT_ROOT / "config" / "agents.yaml"

# API Keys
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# 默认模型配置
DEFAULT_MODEL = "qwen3-max"
DEFAULT_MAX_ITERS = 30

# 日志配置
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
