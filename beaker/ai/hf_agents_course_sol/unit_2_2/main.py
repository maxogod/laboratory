# from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
# import os

# hf_token = os.getenv("HF_TOKEN")

# llm = HuggingFaceInferenceAPI(
#     model_name="Qwen/Qwen2.5-Coder-32B-Instruct",
#     temperature=0.7,
#     max_tokens=100,
#     token=hf_token,
#     provider="auto"
# )

# response = llm.complete("Hello, how are you?")
# print(response)

from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
import asyncio

def multiply(a: int, b: int) -> int:
    """Multiplies two integers and returns the resulting integer"""
    return a * b

llm = HuggingFaceInferenceAPI(model_name="Qwen/Qwen2.5-Coder-32B-Instruct")

agent = AgentWorkflow.from_tools_or_functions(
    [FunctionTool.from_defaults(multiply)],
    llm=llm,
)

async def run():
    # stateless
    response = await agent.run("What is 2 times 2?")
    print(f"1 - {response}")

    # remembering state

    ctx = Context(agent)

    response = await agent.run("My name is Bob.", ctx=ctx)
    print(f"2 - {response}")
    response = await agent.run("What was my name again?", ctx=ctx)
    print(f"3 - {response}")

if __name__ == "__main__":
    asyncio.run(run())
