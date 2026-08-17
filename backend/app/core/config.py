from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ai_provider: str = "race"  # "ollama" | "anthropic_cli" | "race"

    ai_api_key: str = ""
    ai_model: str = "llama3.1"
    ai_base_url: str = "http://localhost:11434/v1"

    anthropic_cli_model: str = "sonnet"

    whisper_model: str = "medium"

    friday_host: str = "127.0.0.1"
    friday_port: int = 8765

    wake_word: str = "friday"
    tts_voice: str = "en-US-AriaNeural"


settings = Settings()
