from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    """
    Global application settings.
    Uses pydantic-settings to load values from .env file or environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    # --- App ---
    APP_NAME: str = "MiniTMS"
    DEBUG: bool = True

    # --- Trans.eu Credentials ---
    TRANS_EU_USERNAME: str = Field(default="", description="Login email for Trans.eu")
    TRANS_EU_PASSWORD: str = Field(default="", description="Password for Trans.eu")
    
    # --- Scraping Settings ---
    HEADLESS_MODE: bool = Field(default=False, description="Run browser in headless mode")
    BROWSER_PROFILE_DIR: str = Field(
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../browser_profile")),
        description="Path to Chrome user data directory for persistent sessions"
    )

# Global instance
settings = Settings()
