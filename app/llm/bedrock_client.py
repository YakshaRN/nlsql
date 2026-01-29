import boto3
import json

class BedrockClient:
    def __init__(self, region="us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def invoke(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 800,
                "temperature": 0
            })
        )

        raw = json.loads(response["body"].read())
        return json.loads(raw["content"][0]["text"])
