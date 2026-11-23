from huggingface_hub import login
import os

HF_TOKEN = os.getenv("HF_TOKEN")

login(HF_TOKEN)

from smolagents import ToolCallingAgent, WebSearchTool, InferenceClientModel

model = InferenceClientModel(
    model_id="HuggingFaceH4/zephyr-7b-beta"
)

agent = ToolCallingAgent(tools=[WebSearchTool()], model=model)

agent.run("Search for the best music recommendations for a party at the Wayne's mansion.")
