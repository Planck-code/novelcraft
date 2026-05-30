from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env file before reading any env vars
load_dotenv(BASE_DIR / '.env')


class Settings:
    # --- App ---
    app_name: str = os.getenv('APP_NAME', '网文 AI 分析助手')
    app_env: str = os.getenv('APP_ENV', 'development')
    database_url: str = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "app.db"}')
    data_dir: Path = Path(os.getenv('DATA_DIR', str(BASE_DIR / 'data')))
    uploads_dir: Path = data_dir / 'uploads'
    novels_dir: Path = data_dir / 'novels'
    analysis_results_dir: Path = data_dir / 'analysis_results'
    prompts_dir: Path = BASE_DIR / 'prompts'
    secret_key: str = os.getenv('SECRET_KEY', 'change-me')

    # --- LLM Provider defaults ---
    llm_default_provider: str = os.getenv('LLM_DEFAULT_PROVIDER', 'openai')
    llm_default_model: str = os.getenv('LLM_DEFAULT_MODEL', 'gpt-4o-mini')

    # --- API Keys ---
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    openai_base_url: str = os.getenv('OPENAI_BASE_URL', '')
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')
    deepseek_base_url: str = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')

    # --- Task queue ---
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    retry_base_delay_seconds: float = float(os.getenv('RETRY_BASE_DELAY', '2.0'))
    max_queue_workers: int = int(os.getenv('MAX_QUEUE_WORKERS', '2'))

    # --- Analysis limits ---
    max_context_chars: int = int(os.getenv('MAX_CONTEXT_CHARS', '8000'))
    max_prompt_tokens_estimate: int = int(os.getenv('MAX_PROMPT_TOKENS', '12000'))


settings = Settings()
