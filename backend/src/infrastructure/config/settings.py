from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os

class Settings(BaseSettings):
    """
    Global application settings.
    Uses pydantic-settings to load values from .env file or environment variables.
    """
    model_config = SettingsConfigDict(
        # backend/.env first for Docker (mount .:/app); .env for local run from backend/
        env_file=("backend/.env", ".env", "../.env"),
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

    # --- GPS Dozor Credentials ---
    GPS_DOZOR_URL: str = Field(default="https://a1.gpsguard.eu/api/v1/vehicle/", description="Base URL for GPS Dozor API")
    GPS_DOZOR_USERNAME: str = Field(default="", description="Login for GPS Dozor")
    GPS_DOZOR_PASSWORD: str = Field(default="", description="Password for GPS Dozor")

    # --- GPS Guard Service ---
    GPS_GUARD_BASE_URL: str = Field(default="https://a1.gpsguard.eu/api/v1", description="Base URL for GPS Guard API")
    GPS_GUARD_API_KEY: str = Field(default="", description="API Key for GPS Guard")

    # --- Profitability Threshold ---
    MIN_ACCEPTABLE_RATE: float = Field(
        default=0.15,
        description="Minimum acceptable profitability rate in EUR/km (allowed range: 0.15..3.5)."
    )
    MOBILE_REMEMBER_ME_DAYS: int = Field(
        default=30,
        description="Remember-me duration for mobile sessions in days."
    )
    MOBILE_PUSH_COOLDOWN_SECONDS: int = Field(
        default=300,
        description="Minimum cooldown between grouped mobile push notifications."
    )

    @field_validator("MIN_ACCEPTABLE_RATE")
    @classmethod
    def validate_min_acceptable_rate(cls, value: float) -> float:
        if value < 0.15 or value > 3.5:
            raise ValueError("MIN_ACCEPTABLE_RATE must be in range 0.15..3.5")
        return value

    @field_validator("MOBILE_REMEMBER_ME_DAYS")
    @classmethod
    def validate_mobile_remember_me_days(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MOBILE_REMEMBER_ME_DAYS must be greater than 0")
        return value

    @field_validator("MOBILE_PUSH_COOLDOWN_SECONDS")
    @classmethod
    def validate_mobile_push_cooldown_seconds(cls, value: int) -> int:
        if value < 300:
            raise ValueError("MOBILE_PUSH_COOLDOWN_SECONDS must be at least 300")
        return value

# Global instance
settings = Settings()
