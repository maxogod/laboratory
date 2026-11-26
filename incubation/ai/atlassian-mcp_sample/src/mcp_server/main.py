import mcp_server.integrations.bitbucket
import mcp_server.integrations.jira
import mcp_server.integrations.storybook  # noqa: F401
from mcp_server.core.server import mcp


def main() -> None:
    """Entry point for the atlassian-mcp server."""
    mcp.run()


if __name__ == "__main__":
    main()
