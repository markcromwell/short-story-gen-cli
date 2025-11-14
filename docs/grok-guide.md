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
storygen generate "A time traveler's dilemma" --provider xai/grok-2-1212 --structured
```

## Available Grok Models

- `xai/grok-2-1212` - Latest stable Grok model (recommended)
- `xai/grok-beta` - Beta version with cutting-edge features
- `xai/grok-4-fast-reasoning` - Fast reasoning model (experimental)

## Example Usage

### Direct Generation

```bash
# Quick story generation
storygen generate "A robot learns to paint" --provider xai/grok-2-1212 --structured --format json > robot-story.json

# Generate with specific parameters
storygen generate "A space adventure" --provider xai/grok-2-1212 --structured --min-words 3000 --pov first_person --epub space-adventure.epub
```

### Editorial Workflow with Grok

```bash
# Generate initial story
storygen generate "A cyberpunk hacker discovers a conspiracy" --provider xai/grok-2-1212 --structured --format json > hacker-story.json

# Start editorial analysis
storygen job start --prose hacker-story.json --output feedback.json

# Apply AI improvements (Grok can improve its own work!)
storygen edit revise --feedback feedback.json --input hacker-story.json --output improved-hacker-story.json
```

## Cost Comparison (approximate)

| Provider | Cost per 1M tokens | Speed | Context Window |
|----------|-------------------|-------|----------------|
| **Grok** | ~$2-5 | Fast ⚡ | 128K+ |
| GPT-4 | ~$30 | Medium | 128K |
| Claude 3 Sonnet | ~$15 | Medium | 200K |
| Ollama | Free 🎉 | Variable | 4K-128K |

## Tips

- Use `--min-words` to control story length and cost
- Grok's large context window is great for complex prompts with backstory
- Test with Ollama locally first, then use Grok for production quality
- The editorial workflow lets Grok improve its own stories iteratively

## Troubleshooting

If you get an authentication error:
1. Check your `.env` file has `XAI_API_KEY=...`
2. Verify your API key is valid at https://console.x.ai
3. Make sure you have credits on your account

## Cost Tracking

The CLI includes built-in cost tracking for Grok models:

```bash
# Generate with cost control
storygen generate "A detective story" --provider xai/grok-2-1212 --structured --max-cost 1.00

# Check costs in verbose output
storygen generate "A mystery" --provider xai/grok-2-1212 --structured --verbose
```

This helps you stay within budget when using premium AI models.
