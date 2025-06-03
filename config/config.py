import yaml
import os
from typing import Dict
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import typer

# Define Pydantic models matching config.yaml structure
class LoggerConfig(BaseModel):
    level: str

class RouterConfig(BaseModel):
    port: int

class SQLWriteConfig(BaseModel):
    host: str
    port: str
    user: str
    password: str
    database: str

class SQLConfig(BaseModel):
    write: SQLWriteConfig

class GeneralConfig(BaseModel):
    logger: LoggerConfig
    router: RouterConfig
    sql: SQLConfig

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

# class ApplicationMessages(BaseModel):
#     en: ApplicationMessagesLang

class Config(BaseSettings):
    """
    Main Config class that loads all configuration.
    Supports env var overrides with prefix POLICY_ and nested keys with '__'.
    """
    current_lang: str
    general: GeneralConfig
    # sql: SQLConfig
    # redis: RedisConfig

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    ApplicationMessages: Dict[str, ApplicationMessagesLang]

    model_config = SettingsConfigDict(
        env_prefix="POLICY_",
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="allow"
    )

    @classmethod
    def load_yaml(cls, filepath: str) -> dict:
        with open(filepath, "r") as f:
            content = os.path.expandvars(f.read())
            return yaml.safe_load(content)

def load_config(config_file: str = "config.yaml") -> Config:

    yaml_data = Config.load_yaml(config_file)

    # Convert environment variables to nested dict
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith("POLICY_"):
            # Remove prefix and split by delimiter
            parts = key.replace("POLICY_", "").lower().split("__")
            current = env_vars
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

    # Recursively update yaml_data with environment variables
    def recursive_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                recursive_update(d[k], v)
            elif v is not None:
                d[k] = v
        return d

    # Merge YAML data with environment variables
    merged = recursive_update(yaml_data, env_vars)

    # Log the merged configuration for debugging
    # logging.info(f"Merged Configuration: {merged}")

    # Create final config
    return Config.model_validate(merged) 



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
    print("SQL Host:", cfg.general.sql.write.host)
    print("JWT Secret:", cfg.JWT_SECRET_KEY)
    print("User Not Found Msg:", cfg.ApplicationMessages.en.UserNotFound.Message)

    # Example error key check
    error_key = "USER_NOT_FOUND"
    if error_key == cfg.ApplicationMessages.en.UserNotFound.Key:
        print("Handle user not found error")

if __name__ == "__main__":
    app() 