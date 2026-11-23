from smolagents import LiteLLMModel, ChatMessage, MessageRole

model = LiteLLMModel(
    model_id="ollama_chat/qwen2:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
)

messages: list[ChatMessage | dict] = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=[{"type": "text", "text": "You are a helpful assistant."}],
    ),
    ChatMessage(
        role=MessageRole.USER,
        content=[{"type": "text", "text": "What is the capital of France?"}],
    ),
]

ans = model.generate(messages=messages)

print(ans.content)
