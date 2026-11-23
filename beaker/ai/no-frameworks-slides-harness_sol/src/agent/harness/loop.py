import logging

from agent.harness.context import Context
from agent.model.base import ModelClient
from agent.tools.registry import ToolRegistry

log = logging.getLogger("agent")


def run(ctx: Context, model: ModelClient, registry: ToolRegistry, max_iterations: int) -> str:
    """Call the model, execute its tool calls, repeat until it answers without tool calls."""
    tools = registry.schemas()

    for step in range(1, max_iterations + 1):
        response = model.complete(ctx.messages, tools)
        ctx.add_assistant(response)

        if not response.tool_calls:
            log.info("step %d: finished", step)
            return response.content

        for call in response.tool_calls:
            log.info("step %d: %s(%s)", step, call.name, ", ".join(f"{k}=..." for k in call.arguments))
            result = registry.execute(call.name, call.arguments)
            log.debug("result: %s", result[:500])
            ctx.add_tool_result(call.id, result)

    raise RuntimeError(f"agent did not finish within {max_iterations} iterations")
