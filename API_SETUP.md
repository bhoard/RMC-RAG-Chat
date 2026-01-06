# Claude API Setup Guide

This guide will help you get a Claude API key for the RAG query system.

## Step 1: Create an Anthropic Account

1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Click "Sign Up" and create an account
3. Verify your email address

## Step 2: Get Your API Key

1. Log into the [Anthropic Console](https://console.anthropic.com/)
2. Navigate to **API Keys** in the left sidebar
3. Click **"Create Key"**
4. Give it a name (e.g., "RMC RAG Chat")
5. Copy the API key (it starts with `sk-ant-...`)
6. **Important**: Save this key securely - you won't be able to see it again!

## Step 3: Add Credits to Your Account

Claude API is pay-as-you-go:
1. In the console, go to **Settings** → **Billing**
2. Add a payment method
3. Purchase credits (minimum $5)
4. Pricing: ~$3 per million input tokens, ~$15 per million output tokens for Sonnet 4

**Typical costs for RMC RAG queries:**
- Each query: ~$0.001 - $0.005 (0.1 to 0.5 cents)
- 1000 queries: ~$1-5 depending on complexity

## Step 4: Configure Your Project

**Option A: Environment Variable (Recommended)**

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Reload your shell
source ~/.bashrc

# Or set temporarily for one session
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

**Option B: Settings File (Less Secure)**

Edit `settings.yaml`:
```yaml
rag:
  claude_api_key: "sk-ant-your-key-here"
```

⚠️ **Warning**: Don't commit this to Git! The key is already in `.gitignore`

## Step 5: Install Required Packages

```bash
source venv/bin/activate
pip install anthropic python-dotenv
```

## Step 6: Test Your Setup

```bash
# Simple test query
make query Q="What is Randolph-Macon College?"

# Or directly
python3 5_rag_query.py "What is Randolph-Macon College?"
```

## Troubleshooting

**"No API key found" error:**
- Check that your environment variable is set: `echo $ANTHROPIC_API_KEY`
- Make sure you've activated your virtual environment: `source venv/bin/activate`
- Try setting the key in `settings.yaml` as a backup

**"Authentication error":**
- Verify your API key is correct (starts with `sk-ant-`)
- Check that you've added credits to your Anthropic account
- Make sure the key hasn't been revoked

**"Rate limit" error:**
- You're making too many requests too quickly
- Wait a moment and try again
- Consider upgrading your Anthropic tier if this persists

## Security Best Practices

1. **Never commit API keys to Git** - They're in `.gitignore` for this reason
2. **Use environment variables** in production
3. **Rotate keys periodically** - Create new keys in the Anthropic console
4. **Set usage limits** in the Anthropic console to prevent unexpected charges
5. **Monitor usage** regularly in the console

## Cost Management

To keep costs low:
- Set a monthly budget in Anthropic console
- Start with a small credit amount ($5-10)
- Monitor usage in the Anthropic console
- The `top_k_chunks` setting controls how much context is sent (lower = cheaper)

## Next Steps

Once your API key is working:
1. Try different questions about RMC
2. Adjust `top_k_chunks` in `settings.yaml` to tune retrieval quality
3. Modify the `system_prompt` to customize Claude's personality
4. Monitor costs and adjust as needed

For more information, see the [Anthropic API Documentation](https://docs.anthropic.com/).
