from config.settings import Settings, TestingSettings, BaseAppSettings
import os

def get_settings() -> BaseAppSettings:
    environment = os.getenv("ENVIRONMENT", "developing")

    if environment == "testing":
        return TestingSettings()
    return Settings()
