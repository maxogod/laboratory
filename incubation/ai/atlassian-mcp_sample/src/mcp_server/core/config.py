from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    atlassian_email: str | None = None

    jira_base_url: str | None = None
    jira_api_token: str | None = None

    bitbucket_workspace: str | None = None
    bitbucket_token: str | None = None

    @property
    def is_jira_enabled(self) -> bool:
        return bool(self.jira_base_url and self.atlassian_email and self.jira_api_token)

    @property
    def is_bitbucket_enabled(self) -> bool:
        return bool(
            self.bitbucket_workspace and self.atlassian_email and self.bitbucket_token
        )


settings = Settings()
