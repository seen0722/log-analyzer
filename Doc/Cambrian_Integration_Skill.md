---
name: Cambrian LLM Integration
description: Connect to internal Cambrian LLM Gateway as a drop-in replacement for OpenAI
---

# Cambrian LLM Integration Skill

This skill enables AI applications to connect to **Pegatron's internal Cambrian LLM Gateway** instead of external OpenAI APIs.

## Architecture

```
┌───────────────────┐     HTTPS (SSL skip)     ┌────────────────────────────────┐
│  Your Application │ ─────────────────────────▶│  Cambrian LLM Gateway          │
│                   │                           │  https://api.cambrian.pegatroncorp.com
│  OpenAI SDK       │                           │                                │
│  (with custom     │                           │  Available Models:             │
│   base_url)       │                           │    - LLAMA 3.3 70B             │
└───────────────────┘                           │    - LLAMA 3.1 8B Instruct     │
                                                │    - Qwen 2.5                  │
                                                └────────────────────────────────┘
```

## Key Differences from OpenAI

| Feature | OpenAI | Cambrian |
|---------|--------|----------|
| Base URL | `https://api.openai.com/v1` | `https://api.cambrian.pegatroncorp.com/v1` |
| SSL | Standard verification | **Disabled** (self-signed cert) |
| Model List API | `GET /v1/models` | `GET /assistant/llm_model` |
| Authentication | Same Bearer token format | Same Bearer token format |

---

## Implementation

### Python (OpenAI SDK)

```python
import httpx
from openai import OpenAI

def create_cambrian_client(api_token: str, base_url: str = "https://api.cambrian.pegatroncorp.com") -> OpenAI:
    """
    Create OpenAI-compatible client for Cambrian LLM Gateway.
    
    Args:
        api_token: API token from Cambrian Portal
        base_url: Cambrian gateway URL (defaults to production)
    
    Returns:
        OpenAI client configured for Cambrian
    """
    # Disable SSL verification for internal self-signed certificate
    http_client = httpx.Client(verify=False)
    
    # Ensure URL ends with /v1 for OpenAI compatibility
    if not base_url.endswith('/v1'):
        base_url = f"{base_url.rstrip('/')}/v1"
    
    return OpenAI(
        base_url=base_url,
        api_key=api_token,
        http_client=http_client
    )

# Usage
client = create_cambrian_client("your-api-token")
response = client.chat.completions.create(
    model="LLAMA 3.3 70B",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

### Complete LLM Client Class

```python
import json
import httpx
from openai import OpenAI

class CambrianLLMClient:
    """LLM client for internal Cambrian gateway with SSL verification disabled."""
    
    def __init__(
        self, 
        base_url: str = "https://api.cambrian.pegatroncorp.com",
        api_key: str = "",
        model: str = "LLAMA 3.3 70B"
    ):
        # Disable SSL verification
        http_client = httpx.Client(verify=False)
        
        # Normalize URL
        if base_url and not base_url.endswith('/v1'):
            base_url = f"{base_url.rstrip('/')}/v1"
        
        self.client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Send chat completion request."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def chat_json(self, messages: list, temperature: float = 0.7) -> dict:
        """Send chat completion with JSON response format."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

### JavaScript/TypeScript (OpenAI SDK)

```typescript
import OpenAI from 'openai';
import https from 'https';

// Create HTTPS agent that ignores SSL verification
const httpsAgent = new https.Agent({ rejectUnauthorized: false });

const cambrian = new OpenAI({
  baseURL: 'https://api.cambrian.pegatroncorp.com/v1',
  apiKey: 'your-api-token',
  httpAgent: httpsAgent,
});

async function chat(prompt: string): Promise<string> {
  const response = await cambrian.chat.completions.create({
    model: 'LLAMA 3.3 70B',
    messages: [{ role: 'user', content: prompt }],
  });
  return response.choices[0].message.content ?? '';
}
```

### cURL

```bash
# List available models
curl -k -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.cambrian.pegatroncorp.com/assistant/llm_model

# Chat completion
curl -k -X POST https://api.cambrian.pegatroncorp.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "LLAMA 3.3 70B",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## API Reference

### Get Available Models

```
GET https://api.cambrian.pegatroncorp.com/assistant/llm_model
Authorization: Bearer <token>
```

Response:
```json
{
  "llm_list": [
    {"name": "LLAMA 3.3 70B", "description": "High quality analysis"},
    {"name": "LLAMA 3.1 8B Instruct", "description": "Fast responses"},
    {"name": "Qwen 2.5", "description": "Chinese optimized"}
  ]
}
```

### Chat Completions (OpenAI-compatible)

```
POST https://api.cambrian.pegatroncorp.com/v1/chat/completions
Authorization: Bearer <token>
Content-Type: application/json

{
  "model": "LLAMA 3.3 70B",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

---

## Connection Testing

### Test Script (Python)

```python
#!/usr/bin/env python3
"""Test Cambrian LLM connectivity."""

import httpx
from openai import OpenAI

def test_cambrian(token: str, url: str = "https://api.cambrian.pegatroncorp.com"):
    print("=== Cambrian LLM Connection Test ===\n")
    
    # Test 1: HTTP connectivity
    print("[1/3] Testing HTTP connection...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = httpx.get(f"{url}/assistant/llm_model", headers=headers, verify=False, timeout=10)
        if r.status_code == 200:
            models = r.json().get('llm_list', [])
            print(f"  ✅ Connected. Found {len(models)} models.")
        elif r.status_code == 401:
            print("  ❌ Authentication failed (401)")
            return False
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

    # Test 2: OpenAI client initialization
    print("\n[2/3] Initializing OpenAI client...")
    http_client = httpx.Client(verify=False)
    client = OpenAI(base_url=f"{url}/v1", api_key=token, http_client=http_client)
    print("  ✅ Client initialized")

    # Test 3: LLM response
    print("\n[3/3] Testing LLM response...")
    try:
        response = client.chat.completions.create(
            model="LLAMA 3.3 70B",
            messages=[{"role": "user", "content": "Say hello in one word."}],
            max_tokens=10
        )
        print(f"  ✅ Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"  ❌ LLM call failed: {e}")
        return False

    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_cambrian.py <API_TOKEN>")
        sys.exit(1)
    test_cambrian(sys.argv[1])
```

---

## Configuration Options

### Environment Variables

```bash
# .env
LLM_PROVIDER=cambrian
CAMBRIAN_URL=https://api.cambrian.pegatroncorp.com
CAMBRIAN_TOKEN=your-api-token
CAMBRIAN_MODEL=LLAMA 3.3 70B
```

### Model Selection Guide

| Model | Use Case | Speed | Quality |
|-------|----------|-------|---------|
| `LLAMA 3.3 70B` | Complex analysis, reasoning | Slower | ⭐⭐⭐⭐⭐ |
| `LLAMA 3.1 8B Instruct` | Quick queries, simple tasks | Fast | ⭐⭐⭐ |
| `Qwen 2.5` | Chinese content, translation | Medium | ⭐⭐⭐⭐ |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `SSL: CERTIFICATE_VERIFY_FAILED` | Use `verify=False` in httpx / `rejectUnauthorized: false` in Node |
| `401 Unauthorized` | Regenerate token at [Cambrian Portal](https://cambrian.pegatroncorp.com) |
| `Connection refused` | Check VPN/network access to `api.cambrian.pegatroncorp.com` |
| `Model not found` | Fetch current model list via `/assistant/llm_model` |

---

## Migration from OpenAI

```diff
- from openai import OpenAI
- client = OpenAI(api_key="sk-...")

+ import httpx
+ from openai import OpenAI
+ http_client = httpx.Client(verify=False)
+ client = OpenAI(
+     base_url="https://api.cambrian.pegatroncorp.com/v1",
+     api_key="cambrian-token",
+     http_client=http_client
+ )

# Chat completions work the same way
response = client.chat.completions.create(
-   model="gpt-4o-mini",
+   model="LLAMA 3.3 70B",
    messages=[...]
)
```

---

## Dependencies

```
# Python
pip install openai httpx

# Node.js  
npm install openai
```
