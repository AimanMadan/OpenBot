from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    
    discord_token: SecretStr
    openai_api_key: SecretStr
    model_config = SettingsConfigDict(env_file=".env",
                                      env_file_encoding="utf-8")
    
    
# init
settings = Settings()
