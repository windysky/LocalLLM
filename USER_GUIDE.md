# LocalLLM User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [API Documentation](#api-documentation)
4. [Client Libraries](#client-libraries)
5. [Model Selection](#model-selection)
6. [Chat Completions](#chat-completions)
7. [Text Completions](#text-completions)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

## Introduction

Welcome to LocalLLM! This service provides local language model inference with an OpenAI-compatible API. You can interact with powerful language models like Gemma-2, Qwen2.5, Llama-3.1, and Mistral directly through standard HTTP requests.

### What is LocalLLM?

- **Local Inference**: All models run on local servers, ensuring data privacy
- **OpenAI Compatible**: Use the same API as OpenAI's GPT models
- **Multiple Models**: Choose from various models optimized for different tasks
- **No Authentication**: Simple, direct API access (check with your admin if auth is enabled)

### Key Benefits

- 🔒 **Privacy**: Your data never leaves the local network
- ⚡ **Speed**: Low-latency responses without internet delays
- 💰 **Cost-Effective**: No per-token charges after initial setup
- 🛡️ **Security**: Full control over your AI infrastructure

## Getting Started

### Prerequisites

- The LocalLLM server URL from your administrator
- An HTTP client library (curl, Postman, or programming language)
- Basic understanding of REST APIs

### First API Call

Let's make your first API call to check if the service is accessible:

```bash
curl https://your-llm-server.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": 1703123456,
  "models_loaded": 2
}
```

### Available Models

List all available models:

```bash
curl https://your-llm-server.com/v1/models
```

Response example:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gemma-2-9b",
      "object": "model",
      "created": 1703123456,
      "owned_by": "local"
    },
    {
      "id": "qwen2.5-7b",
      "object": "model",
      "created": 1703123456,
      "owned_by": "local"
    }
  ]
}
```

## API Documentation

### Base URL

```
https://your-llm-server.com
```

### Authentication

Currently, the API does not require authentication. However, if your administrator has enabled API keys:

```bash
curl -H "X-API-Key: your-api-key" \
     https://your-llm-server.com/v1/chat/completions
```

### Common Headers

```bash
curl -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     https://your-llm-server.com/v1/chat/completions
```

## Client Libraries

### Python (Recommended)

Install the OpenAI Python library:

```bash
pip install openai
```

Basic setup:

```python
from openai import OpenAI

# Initialize client
client = OpenAI(
    base_url="https://your-llm-server.com/v1",
    api_key="not-required"  # No auth needed unless configured
)

# Make a request
response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### JavaScript/Node.js

```bash
npm install openai
```

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://your-llm-server.com/v1',
  apiKey: 'not-required' // No auth needed unless configured
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'gemma-2-9b',
    messages: [{ role: 'user', content: 'Hello!' }]
  });
  console.log(response.choices[0].message.content);
}

chat();
```

### cURL (Command Line)

Basic chat completion:

```bash
curl -X POST https://your-llm-server.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-2-9b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Other Languages

The service is compatible with any HTTP client. Here are some popular libraries:

- **Java**: OkHttp, Apache HttpClient
- **C#**: HttpClient, RestSharp
- **Ruby**: HTTParty, Faraday
- **PHP**: Guzzle, cURL
- **Go**: net/http, req
- **Rust**: reqwest, surf

## Model Selection

### Available Models

| Model | Parameters | Best For | Speed | Accuracy |
|-------|------------|----------|-------|----------|
| gemma-2-9b | 9B | General chat, coding | Fast | High |
| qwen2.5-7b | 7B | Multilingual, reasoning | Very Fast | High |
| llama-3.1-8b | 8B | Creative writing, dialogue | Fast | Very High |
| mistral-7b | 7B | Analysis, structured output | Very Fast | High |

### Choosing a Model

- **For speed**: `mistral-7b` or `qwen2.5-7b`
- **For accuracy**: `llama-3.1-8b` or `gemma-2-9b`
- **For multilingual**: `qwen2.5-7b` (supports Chinese, English, and more)
- **For coding**: `gemma-2-9b` or `llama-3.1-8b`

### Model Status Check

Check if a model is loaded:

```bash
curl https://your-llm-server.com/models/status
```

Load a model (if needed):

```bash
curl -X POST https://your-llm-server.com/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma-2-9b"}'
```

## Chat Completions

### Basic Request

```python
response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)
```

### Multi-turn Conversation

```python
response = client.chat.completions.create(
    model="llama-3.1-8b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What about Germany?"}
    ]
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | string | Required | Model name |
| messages | array | Required | List of messages |
| temperature | float | 0.7 | Randomness (0-2) |
| max_tokens | integer | 1024 | Max response length |
| stream | boolean | false | Stream response |

### Advanced Parameters

```python
response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[
        {"role": "user", "content": "Write a story"}
    ],
    temperature=0.9,  # More creative
    max_tokens=2000,  # Longer response
    top_p=0.95,       # Nucleus sampling
    frequency_penalty=0.5,  # Reduce repetition
)
```

### Response Format

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1703123456,
  "model": "gemma-2-9b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The response text..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  }
}
```

## Text Completions

### Basic Request

```python
response = client.completions.create(
    model="mistral-7b",
    prompt="The weather today is",
    max_tokens=100
)
```

### cURL Example

```bash
curl -X POST https://your-llm-server.com/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b",
    "prompt": "Python is a programming language that",
    "max_tokens": 50,
    "temperature": 0.5
  }'
```

### Use Cases

- **Text completion**: Finish partial text
- **Code completion**: Generate code snippets
- **Text summarization**: Condense long texts
- **Translation**: Translate between languages

## Advanced Features

### Streaming Responses

```python
stream = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end='', flush=True)
```

### System Prompts

Set behavior with system messages:

```python
response = client.chat.completions.create(
    model="llama-3.1-8b",
    messages=[
        {
            "role": "system",
            "content": "You are an expert Python developer. Always provide code examples."
        },
        {
            "role": "user",
            "content": "How do I read a CSV file?"
        }
    ]
)
```

### JSON Mode

Request structured output:

```python
response = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[
        {
            "role": "system",
            "content": "Respond only with valid JSON."
        },
        {
            "role": "user",
            "content": "Extract the name and age from: John is 25 years old"
        }
    ]
)
```

### Few-shot Learning

Provide examples in the prompt:

```python
response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[
        {
            "role": "system",
            "content": "Translate English to French. Follow the examples."
        },
        {
            "role": "user",
            "content": "Hello: Bonjour"
        },
        {
            "role": "user",
            "content": "Goodbye: Au revoir"
        },
        {
            "role": "user",
            "content": "Thank you:"
        }
    ]
)
```

## Best Practices

### Prompt Engineering

1. **Be Specific**
   ```python
   # Bad
   messages=[{"role": "user", "content": "Write about AI"}]

   # Good
   messages=[{"role": "user", "content": "Write a 200-word explanation of neural networks for beginners"}]
   ```

2. **Provide Context**
   ```python
   messages=[
       {"role": "system", "content": "You are a math tutor explaining concepts to high school students."},
       {"role": "user", "content": "Explain derivatives"}
   ]
   ```

3. **Chain of Thought**
   ```python
   messages=[
       {"role": "user", "content": "Solve: A train travels 300 miles in 4 hours. What is its speed? Think step by step."}
   ]
   ```

### Performance Optimization

1. **Batch Similar Requests**
   ```python
   # Process multiple related items in one request
   messages=[
       {"role": "user", "content": "Summarize these three articles: [text1], [text2], [text3]"}
   ]
   ```

2. **Choose Right Model**
   - Use smaller models for simple tasks
   - Use larger models for complex reasoning

3. **Cache Responses**
   ```python
   import hashlib
   import json
   import time

   cache = {}

   def cached_completion(prompt):
       key = hashlib.md5(prompt.encode()).hexdigest()
       if key in cache:
           return cache[key]

       response = client.chat.completions.create(
           model="mistral-7b",
           messages=[{"role": "user", "content": prompt}]
       )

       cache[key] = response.choices[0].message.content
       return response.choices[0].message.content
   ```

### Error Handling

```python
from openai import OpenAIError

try:
    response = client.chat.completions.create(
        model="gemma-2-9b",
        messages=[{"role": "user", "content": "Hello"}]
    )
except OpenAIError as e:
    print(f"API Error: {e}")
    # Implement retry logic or fallback
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Rate Limiting

Be mindful of rate limits set by your administrator. Implement backoff:

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def chat_with_retry(prompt):
    return client.chat.completions.create(
        model="gemma-2-9b",
        messages=[{"role": "user", "content": prompt}]
    )
```

## Examples

### Example 1: Chatbot Application

```python
class ChatBot:
    def __init__(self, model="gemma-2-9b"):
        self.client = OpenAI(
            base_url="https://your-llm-server.com/v1",
            api_key="not-required"
        )
        self.model = model
        self.history = []

    def chat(self, message):
        self.history.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history
        )

        reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def clear_history(self):
        self.history = []

# Usage
bot = ChatBot()
print(bot.chat("Hello, who are you?"))
print(bot.chat("What can you do?"))
```

### Example 2: Code Generator

```python
def generate_code(language, description):
    response = client.chat.completions.create(
        model="llama-3.1-8b",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert {language} programmer. Provide clean, commented code."
            },
            {
                "role": "user",
                "content": f"Write a {language} function to: {description}"
            }
        ],
        temperature=0.3  # Lower temperature for more consistent code
    )
    return response.choices[0].message.content

# Usage
python_code = generate_code("Python", "fetch data from a REST API and save to CSV")
print(python_code)
```

### Example 3: Text Summarizer

```python
def summarize_text(text, summary_type="brief"):
    prompts = {
        "brief": "Provide a 2-3 sentence summary",
        "detailed": "Provide a detailed summary in bullet points",
        "executive": "Provide an executive summary for busy stakeholders"
    }

    response = client.chat.completions.create(
        model="qwen2.5-7b",
        messages=[
            {
                "role": "user",
                "content": f"{prompts[summary_type]}: {text}"
            }
        ],
        max_tokens=500
    )
    return response.choices[0].message.content

# Usage
long_text = "Your long article here..."
summary = summarize_text(long_text, "detailed")
print(summary)
```

### Example 4: Language Translator

```python
def translate_text(text, from_lang, to_lang):
    response = client.chat.completions.create(
        model="qwen2.5-7b",  # Good for multilingual tasks
        messages=[
            {
                "role": "system",
                "content": f"You are a professional translator. Translate from {from_lang} to {to_lang}."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.2  # Low temperature for accurate translation
    )
    return response.choices[0].message.content

# Usage
spanish = translate_text("Hello, how are you?", "English", "Spanish")
print(spanish)  # Hola, ¿cómo estás?
```

### Example 5: Sentiment Analysis

```python
def analyze_sentiment(text):
    response = client.chat.completions.create(
        model="mistral-7b",
        messages=[
            {
                "role": "system",
                "content": "Analyze sentiment and respond with only: positive, negative, or neutral"
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.1  # Very low temperature for consistent classification
    )
    return response.choices[0].message.content.strip().lower()

# Usage
sentiment = analyze_sentiment("I love this product! It works perfectly.")
print(f"Sentiment: {sentiment}")  # Sentiment: positive
```

### Example 6: Stream Processing for Web App

```javascript
// Frontend JavaScript for real-time streaming
async function streamChat(message, onChunk) {
    const response = await fetch('https://your-llm-server.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'gemma-2-9b',
            messages: [{ role: 'user', content: message }],
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data !== '[DONE]') {
                    const parsed = JSON.parse(data);
                    const content = parsed.choices[0].delta.content;
                    if (content) {
                        onChunk(content);
                    }
                }
            }
        }
    }
}

// Usage
streamChat("Tell me a joke", (chunk) => {
    document.getElementById('output').innerHTML += chunk;
});
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the server URL is correct
   - Verify the service is running with your administrator
   - Check network connectivity

2. **Model Not Found**
   ```bash
   # Check available models
   curl https://your-llm-server.com/v1/models

   # Load model if needed
   curl -X POST https://your-llm-server.com/models/load \
        -H "Content-Type: application/json" \
        -d '{"model": "gemma-2-9b"}'
   ```

3. **Slow Responses**
   - Try a smaller model (e.g., mistral-7b)
   - Reduce max_tokens in your request
   - Check if the server is under heavy load

4. **Unexpected Responses**
   - Check your prompt is clear and specific
   - Try adjusting the temperature parameter
   - Use system messages to set context

### Debug Mode

Enable debug logging:

```python
import logging
import openai

logging.basicConfig(level=logging.DEBUG)
openai.log = "debug"

# This will show all HTTP requests and responses
```

### Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check your JSON formatting |
| 404 | Not Found | Verify model name and endpoint |
| 429 | Rate Limited | Reduce request frequency |
| 500 | Server Error | Contact administrator |

### Getting Help

1. Check the API documentation at `https://your-llm-server.com/docs`
2. Contact your system administrator
3. Check service status at `https://your-llm-server.com/health`

### Feedback

To report issues or request features:
- Email: support@yourdomain.com
- Internal ticketing system: IT Helpdesk
- Documentation wiki: https://wiki.yourdomain.com/locallm

## Quick Reference

### Essential Endpoints

```bash
# Health check
GET /health

# List models
GET /v1/models

# Chat completion
POST /v1/chat/completions

# Text completion
POST /v1/completions

# Model status
GET /models/status
```

### Code Templates

Python Setup:
```python
from openai import OpenAI
client = OpenAI(
    base_url="https://your-server.com/v1",
    api_key="not-required"
)
```

Basic Chat:
```python
response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

Happy coding with LocalLLM! 🚀