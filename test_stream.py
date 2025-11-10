"""Quick test to verify streaming works with litellm + ollama"""

import litellm

print("Testing streaming with ollama/llama2...")
print("=" * 80)

response = litellm.completion(
    model="ollama/llama2",
    messages=[{"role": "user", "content": "Write a 2-sentence story about a robot."}],
    stream=True,
    max_tokens=100,
)

print("Streaming response:")
for chunk in response:
    if hasattr(chunk, "choices") and chunk.choices:
        delta = chunk.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            print(delta.content, end="", flush=True)

print("\n" + "=" * 80)
print("Done!")
