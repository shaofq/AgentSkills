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

# AIGateway 配置 (OpenAI 兼容接口)
AIGATEWAY_API_KEY = os.environ.get("AIGATEWAY_API_KEY", "")
AIGATEWAY_BASE_URL = os.environ.get("AIGATEWAY_BASE_URL", "")  # 例如: https://aigateway.edgecloudapp.com/v1/{id}/{name}
AIGATEWAY_MODEL = os.environ.get("AIGATEWAY_MODEL", "claude-4.5-sonnet")

# 默认模型配置
DEFAULT_MODEL = "qwen3-max"
DEFAULT_MAX_ITERS = 30

# 模型提供商: "dashscope" 或 "aigateway"
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "dashscope")

# 日志配置
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
