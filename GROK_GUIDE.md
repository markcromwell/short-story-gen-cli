# Using Grok with Story Generator 🚀

xAI's Grok models are **recommended** for this CLI - they're fast, cheap, and have a huge context window!

## Why Grok?

- ⚡ **Fast**: Low latency responses
- 💰 **Cheap**: Cost-effective pricing compared to GPT-4
- 📚 **Large Context**: 128K+ tokens - can handle long prompts
- 🎨 **Creative**: Great for story generation

## Setup

1. Get your API key from https://console.x.ai

2. Add to `.env`:
```bash
XAI_API_KEY=xai-your-key-here
```

3. Generate a story:
```bash
python -m storygen.cli --provider xai/grok-2-1212 "A robot learns to paint"
```

## Available Grok Models

- `xai/grok-2-1212` - Latest stable Grok model (recommended)
- `xai/grok-beta` - Beta version with cutting-edge features

## Example Usage

```bash
# Short story
python -m storygen.cli --provider xai/grok-2-1212 "A time traveler's dilemma"

# Longer story with more tokens
python -m storygen.cli --provider xai/grok-2-1212 --max-tokens 2000 "An epic space saga"

# Quick flash fiction
python -m storygen.cli --provider xai/grok-2-1212 --max-tokens 500 "A mysterious door"
```

## Cost Comparison (approximate)

| Provider | Cost per 1M tokens | Speed | Context Window |
|----------|-------------------|-------|----------------|
| **Grok** | ~$2-5 | Fast ⚡ | 128K+ |
| GPT-4 | ~$30 | Medium | 128K |
| Claude 3 Sonnet | ~$15 | Medium | 200K |
| Ollama | Free 🎉 | Variable | 4K-128K |

## Tips

- Use `--max-tokens` to control story length and cost
- Grok's large context window is great for complex prompts with backstory
- Test with Ollama locally first, then use Grok for production quality

## Troubleshooting

If you get an authentication error:
1. Check your `.env` file has `XAI_API_KEY=...`
2. Verify your API key is valid at https://console.x.ai
3. Make sure you have credits on your account
