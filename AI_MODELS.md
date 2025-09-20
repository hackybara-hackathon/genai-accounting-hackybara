# AI Model Configuration Guide

Your accounting system now supports multiple AI models for receipt classification and business insights generation.

## Supported Models

### 🦙 **Meta Llama Models**
- `meta.llama3-2-1b-instruct-v1:0` - Fastest, lowest cost
- `meta.llama3-2-3b-instruct-v1:0` - **Recommended for most use cases**
- `meta.llama3-2-11b-instruct-v1:0` - Better accuracy for complex receipts
- `meta.llama3-2-90b-instruct-v1:0` - Highest accuracy, slower
- `meta.llama3-1-8b-instruct-v1:0` - Previous generation
- `meta.llama3-1-70b-instruct-v1:0` - Previous generation, high accuracy

### 🎯 **Mistral Models**
- `mistral.mistral-7b-instruct-v0:2` - Good balance of speed and accuracy
- `mistral.mixtral-8x7b-instruct-v0:1` - High performance mixture-of-experts
- `mistral.mistral-large-2402-v1:0` - Latest large model
- `mistral.mistral-large-2407-v1:0` - Most recent, best performance

### ⭐ **Amazon Nova Models** (when available)
- `amazon.nova-micro-v1:0` - Ultra-fast, cost-effective
- `amazon.nova-lite-v1:0` - Balanced performance
- `amazon.nova-pro-v1:0` - Professional-grade accuracy

### 🔍 **DeepSeek Models** (custom integration)
- `deepseek-chat` - General conversation and analysis
- `deepseek-coder` - Code and structured data analysis

### 🧠 **Claude Models** (legacy support)
- `anthropic.claude-3-5-sonnet-20240620-v1:0` - Previous default
- `anthropic.claude-3-haiku-20240307-v1:0` - Fast and efficient

## Model Selection Guidelines

### For Small Businesses (< 100 receipts/month):
**Recommended:** `meta.llama3-2-3b-instruct-v1:0`
- Low cost
- Good accuracy for common receipt types
- Fast processing

### For Medium Businesses (100-1000 receipts/month):
**Recommended:** `mistral.mistral-7b-instruct-v0:2`
- Excellent accuracy
- Good performance
- Reasonable cost

### For Large Businesses (> 1000 receipts/month):
**Recommended:** `meta.llama3-2-11b-instruct-v1:0`
- High accuracy for complex receipts
- Better insights generation
- Scales well

### For Complex Receipt Types:
**Recommended:** `mistral.mistral-large-2407-v1:0`
- Best accuracy for handwritten receipts
- Excellent multi-language support
- Superior insights generation

## Configuration

### Via Environment Variable:
```bash
export MODEL_ID="meta.llama3-2-3b-instruct-v1:0"
```

### Via SAM Template:
```yaml
Parameters:
  ModelId:
    Type: String
    Default: meta.llama3-2-3b-instruct-v1:0
```

### Via AWS Console:
1. Go to Lambda → Your function → Configuration → Environment variables
2. Edit `MODEL_ID` variable
3. Set to desired model ID
4. Save changes

## Performance Comparison

| Model | Speed | Accuracy | Cost | Best For |
|-------|-------|----------|------|----------|
| Llama 3.2 1B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High volume, simple receipts |
| Llama 3.2 3B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **General use** |
| Llama 3.2 11B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Complex receipts |
| Mistral 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Balanced performance |
| Mistral Large | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Maximum accuracy |
| Nova Micro | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cost optimization |
| Claude Sonnet | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Legacy compatibility |

## Region Availability

Ensure your chosen model is available in your AWS region:
- **ap-southeast-1 (Singapore)**: Most Llama and Mistral models
- **us-east-1 (Virginia)**: All models including Nova
- **eu-west-1 (Ireland)**: Most models

## Switching Models

You can switch models without code changes:

1. **Update SAM template** and redeploy:
   ```bash
   sam deploy --parameter-overrides ModelId=meta.llama3-2-11b-instruct-v1:0
   ```

2. **Update environment variable** directly in AWS Lambda console

3. **Test the change** by uploading a receipt and checking logs

## Troubleshooting

### Model Not Available
- Check region availability
- Verify model ID spelling
- Request model access in AWS Bedrock console

### Poor Classification Results
- Try a larger model (3B → 11B → Large)
- Check if receipt text is clear
- Review logs for processing errors

### High Costs
- Switch to smaller model (11B → 3B → 1B)
- Consider Nova models for cost optimization
- Monitor usage in AWS Cost Explorer

## Custom Model Integration

For advanced users, you can add custom models by:
1. Adding model configuration to `bedrock_client.py`
2. Implementing request/response format
3. Testing with sample receipts

Contact support for assistance with custom model integration.