from pathlib import Path

from agent.tools.registry import ToolRegistry


def register(registry: ToolRegistry, workspace: Path) -> None:
    root = workspace.resolve()

    def resolve(rel: str) -> Path:
        """Resolve a workspace-relative path, refusing escapes and non-.html files."""
        path = (root / rel).resolve()
        if not path.is_relative_to(root):
            raise PermissionError(f"path escapes workspace: {rel}")
        if path.suffix.lower() not in (".html", ".htm"):
            raise ValueError("only .html/.htm files are allowed")
        return path

    @registry.tool(
        name="list_html_files",
        description="List all HTML files in the workspace (relative paths).",
        parameters={"type": "object", "properties": {}},
    )
    def list_html_files() -> str:
        files = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.suffix.lower() in (".html", ".htm"))
        return "\n".join(files) or "(no HTML files)"

    @registry.tool(
        name="read_html_file",
        description="Read an HTML file from the workspace.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "workspace-relative path"}},
            "required": ["path"],
        },
    )
    def read_html_file(path: str) -> str:
        return resolve(path).read_text()

    @registry.tool(
        name="write_html_file",
        description="Create or overwrite an HTML file in the workspace. Parent directories are created.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "workspace-relative path, e.g. slides/deck.html"},
                "content": {"type": "string", "description": "full file contents"},
            },
            "required": ["path", "content"],
        },
    )
    def write_html_file(path: str, content: str) -> str:
        target = resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"Wrote {len(content)} chars to {target.relative_to(root)}"
