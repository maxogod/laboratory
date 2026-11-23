from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langchain_groq import ChatGroq
from tools import search_tool, weather_info_tool, hub_stats_tool
from retriever import guest_info_tool
import os
from pydantic.types import SecretStr

GROQ_API_KEY = SecretStr(os.getenv("GROQ_API_KEY", ""))


chat = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=GROQ_API_KEY,
    max_tokens=300,
)

tools = [guest_info_tool, search_tool, weather_info_tool, hub_stats_tool]
chat_with_tools = chat.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def assistant(state: AgentState):
    return {
        "messages": [chat_with_tools.invoke(state["messages"])],
    }

# --- GRAPH ---

builder = StateGraph(AgentState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition, # If the latest message requires a tool, route to tools Otherwise, provide a direct response
)
builder.add_edge("tools", "assistant")

alfred = builder.compile()

# --- USAGE ---

response = alfred.invoke({"messages": "Tell me about 'Lady Ada Lovelace'"}) # type: ignore
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")

response = alfred.invoke({"messages": "What's the weather like in Paris tonight? Will it be suitable for our fireworks display?"}) # type: ignore
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")

response = alfred.invoke({"messages": "One of our guests is from Qwen. What can you tell me about their most popular model?"}) # type: ignore
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")

response = alfred.invoke({"messages":"I need to speak with 'Dr. Nikola Tesla' about recent advancements in wireless energy. Can you help me prepare for this conversation?"}) # type: ignore
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")

# MEMORY:

response = alfred.invoke({"messages": [HumanMessage(content="Tell me about 'Lady Ada Lovelace'. What's her background and how is she related to me?")]})
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")
print()

response = alfred.invoke({"messages": response["messages"] + [HumanMessage(content="What projects is she currently working on?")]})
print("🎩 Alfred's Response:")
print(response['messages'][-1].content, end="\n\n")
