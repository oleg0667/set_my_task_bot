from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DB_URL: str = "sqlite+aiosqlite:///./tasks.db"

    # Proxy settings (optional, for regions where Telegram API is blocked)
    PROXY_ENABLED: bool = False
    PROXY_PROTOCOL: str = "socks5"
    PROXY_HOST: str = ""
    PROXY_PORT: int = 0
    PROXY_LOGIN: str = ""
    PROXY_PASSWORD: str = ""

    @property
    def proxy_url(self) -> str | None:
        if not self.PROXY_ENABLED or not self.PROXY_HOST:
            return None
        if self.PROXY_LOGIN:
            return f"{self.PROXY_PROTOCOL}://{self.PROXY_LOGIN}:{self.PROXY_PASSWORD}@{self.PROXY_HOST}:{self.PROXY_PORT}"
        return f"{self.PROXY_PROTOCOL}://{self.PROXY_HOST}:{self.PROXY_PORT}"


settings = Settings()
