import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": "Reply with only the word OK"
            }
        ],
        "max_tokens": 10,
        "temperature": 0
    })
)
raw = json.loads(response["body"].read())
print(raw["content"][0]["text"])
