from config import Config
from utils import Logger
from utils.cache_handler import CacheHandler
from utils.email_service import EmailService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class Common:
    _config = None
    _logger = None
    _cache_handler = None
    _email_service = None
    _engine = None
    _async_session = None

    @classmethod
    def config(cls):
        if cls._config is None:
            cls._config = Config()
        return cls._config

    @classmethod
    def logger(cls):
        if cls._logger is None:
            cls._logger = Logger("ActivityApp")
        return cls._logger

    @classmethod
    def cache_handler(cls):
        if cls._cache_handler is None:
            redis_conf = cls.config().get('redis')['write']
            redis_url = f"redis://:{redis_conf['password']}@{redis_conf['host']}:{redis_conf['port']}/{redis_conf['database']}"
            cls._cache_handler = CacheHandler(redis_url=redis_url)
        return cls._cache_handler

    @classmethod
    def email_service(cls):
        if cls._email_service is None:
            cfg = cls.config().get('SendGridAPIKey'), cls.config().get('SendGridFromEmail'), cls.config().get('SendGridFromName')
            cls._email_service = EmailService(*cfg)
        return cls._email_service

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            db_conf = cls.config().get('sql')['write']
            DATABASE_URL = f"mysql+aiomysql://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
            cls._engine = create_async_engine(DATABASE_URL, echo=True)
        return cls._engine

    @classmethod
    def get_async_session(cls) -> AsyncSession:
        if cls._async_session is None:
            engine = cls.get_engine()
            cls._async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        return cls._async_session() 