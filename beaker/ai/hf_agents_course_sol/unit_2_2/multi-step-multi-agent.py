from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, Event, step
from llama_index.core.agent import ReActAgent
from llama_index.llms.groq import Groq
import asyncio
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = Groq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=GROQ_API_KEY,
    max_tokens=300,
)

# Tools
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

add_tool = FunctionTool.from_defaults(add)
multiply_tool = FunctionTool.from_defaults(multiply)

# Agents
planner = ReActAgent(
    tools=[],
    llm=llm,
    system_prompt="You are a planning agent. Break user requests into steps."
)

worker = ReActAgent(
    tools=[add, multiply],
    llm=llm,
    system_prompt="You execute math tasks."
)

critic = ReActAgent(
    tools=[],
    llm=llm,
    system_prompt="You review outputs and improve them."
)

# Workflow
class PlanEvent(Event):
    plan: str

class WorkEvent(Event):
    task: str

class ReviewEvent(Event):
    output: str

class MultiAgentWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.planner = planner
        self.worker = worker
        self.critic = critic

    @step
    async def plan(self, ev: StartEvent) -> PlanEvent:
        print(f"Planning for input: {ev.input}")
        plan = await self.planner.run(f"DONT SOLVE THIS PROBLEM, but make a simple solution plan in words: {ev.input}")
        print(f"Plan generated: {plan}")
        return PlanEvent(plan=str(plan))

    @step
    async def work(self, ev: PlanEvent) -> ReviewEvent:
        print(f"Working on plan")
        result = await self.worker.run(ev.plan)
        print(f"Work result: {result}")
        return ReviewEvent(output=str(result))

    @step
    async def review(self, ev: ReviewEvent) -> StopEvent:
        print(f"Reviewing output: {ev.output}")
        final = await self.critic.run(f"Express this number as result of the asked operation (even if you dont know the operation): {ev.output}")
        print(f"Final output: {final}")
        return StopEvent(result=str(final))

async def main():
    workflow = MultiAgentWorkflow()
    result = await workflow.run(input="What is (2 + 3) * 4?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
