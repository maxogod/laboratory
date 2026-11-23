# Web agent
from smolagents import CodeAgent, DuckDuckGoSearchTool, InferenceClientModel

agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=InferenceClientModel(
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct"
    )
)

# Multi-agent
from smolagents import ToolCallingAgent, CodeAgent, DuckDuckGoSearchTool, InferenceClientModel

web_agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool()],
    model=InferenceClientModel(
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct"
    ),
    max_steps=3,
    name="WebAgent",
    description="An agent that can search the web for information."
)

manager_agent = CodeAgent(
    tools=[],
    model=InferenceClientModel(
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct"
    ),
    max_steps=5,
    name="ManagerAgent",
    description="An agent that manages the web agent and processes the information it retrieves.",
    managed_agents=[web_agent]
)

# Security restrictions
from smolagents import InferenceClientModel, CodeAgent

agent = CodeAgent(
    tools=[],
    model=InferenceClientModel(
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct"
        ),
    max_steps=5,
    additional_authorized_imports=["datetime"],
)

# prompt = "What is the capital of France?"
# agent.run(prompt)
