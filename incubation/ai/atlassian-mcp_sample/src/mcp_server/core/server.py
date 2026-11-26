from fastmcp import FastMCP

mcp = FastMCP("atlassian-mcp")

READ_ONLY = {"readOnlyHint": True}
CREATES_CONTENT = {"readOnlyHint": False, "destructiveHint": False}
OVERWRITES_CONTENT = {"readOnlyHint": False, "destructiveHint": True}
