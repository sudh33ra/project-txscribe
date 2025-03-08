from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Meeting Minutes API"
    
    # Add your configurations here
    WHISPER_MODEL: str = "base"
    SUMMARIZATION_MODEL: str = "t5-small"
    
    class Config:
        case_sensitive = True

settings = Settings() 