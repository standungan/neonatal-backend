from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Neonatal Care System"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str

    database_url: str

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    storage_backend: str = "local"
    storage_local_path: str = "./uploads"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bucket_name: str = ""
    aws_region: str = "ap-southeast-1"

    allowed_origins: str = "http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
