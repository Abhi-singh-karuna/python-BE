import yaml
import os
from typing import Dict
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import typer

# Define Pydantic models matching config.yaml structure
class LoggerConfig(BaseModel):
    level: str

class RouterConfig(BaseModel):
    port: int

class GeneralConfig(BaseModel):
    logger: LoggerConfig
    router: RouterConfig

class SQLWriteConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str

class RedisWriteConfig(BaseModel):
    host: str
    port: int
    password: str
    database: int

class SQLConfig(BaseModel):
    write: SQLWriteConfig

class RedisConfig(BaseModel):
    write: RedisWriteConfig

class MessageFormat(BaseModel):
    Key: str
    Message: str

class ApplicationMessagesLang(BaseModel):
    UserNotFound: MessageFormat
    DuplicateUser: MessageFormat
    InvalidCredentials: MessageFormat
    InvalidToken: MessageFormat
    TokenExpired: MessageFormat
    InternalServerError: MessageFormat

class ApplicationMessages(BaseModel):
    en: ApplicationMessagesLang

class Config(BaseSettings):
    """
    Main Config class that loads all configuration.
    Supports env var overrides with prefix ABHI_ and nested keys with '__'.
    """
    general: GeneralConfig
    sql: SQLConfig
    redis: RedisConfig

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    ApplicationMessages: ApplicationMessages

    class Config:
        env_prefix = "ABHI_"
        env_nested_delimiter = "__"
        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def load_yaml(cls, filepath: str) -> dict:
        with open(filepath, "r") as f:
            # Expand environment variables in the YAML content
            content = os.path.expandvars(f.read())
            return yaml.safe_load(content)

def load_config(config_file: str = "config.yaml") -> Config:
    """
    Load the config from YAML + environment variables.
    Env vars override YAML values.
    """
    # Load YAML config as dict
    yaml_data = Config.load_yaml(config_file)
    # Let Pydantic merge env vars automatically
    return Config.model_validate(yaml_data)

# CLI tool for testing or config overrides
app = typer.Typer(help="Config loader CLI with env var and YAML support.")

@app.command()
def main(
    config_file: str = typer.Option("config.yaml", help="Path to config YAML file"),
    log_level: str = typer.Option(None, help="Override log level"),
):
    """
    Load config and print some values for demonstration.
    """
    cfg = load_config(config_file=config_file)

    # Override log level from CLI flag if provided
    if log_level:
        cfg.general.logger.level = log_level

    print("Logger Level:", cfg.general.logger.level)
    print("SQL Host:", cfg.sql.write.host)
    print("JWT Secret:", cfg.JWT_SECRET_KEY)
    print("User Not Found Msg:", cfg.ApplicationMessages.en.UserNotFound.Message)

    # Example error key check
    error_key = "USER_NOT_FOUND"
    if error_key == cfg.ApplicationMessages.en.UserNotFound.Key:
        print("Handle user not found error")

if __name__ == "__main__":
    app() 