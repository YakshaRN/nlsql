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
                "max_tokens": 2048,
                "temperature": 0
            })
        )

        raw = json.loads(response["body"].read())
        text = raw["content"][0]["text"]
        
        # Try to parse as JSON directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # LLM might wrap JSON in markdown code blocks, try to extract
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON object in the text
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group(0))
            
            # If all else fails, return as explanation
            return {
                "explanation": text,
                "sql": "",
                "assumptions": "Could not parse structured response from LLM"
            }
