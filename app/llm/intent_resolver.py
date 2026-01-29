from .bedrock_client import BedrockClient
from .prompts import SYSTEM_PROMPT, build_user_prompt
from app.queries.registry import QUERY_REGISTRY

class IntentResolver:
    def __init__(self):
        self.llm = BedrockClient()

    def resolve(self, question: str, context: dict | None):
        prompt = build_user_prompt(question, QUERY_REGISTRY, context)
        return self.llm.invoke(SYSTEM_PROMPT, prompt)
