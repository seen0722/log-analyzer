import httpx
import os
from openai import AsyncOpenAI

async def test_api_connection(provider, api_key):
    """
    Tests the connection to the specified LLM provider.
    Returns (True, message) or (False, error_message)
    """
    try:
        if provider == "cambrian":
            # Test Cambrian Connection (List Models)
            final_key = api_key or os.getenv("CAMBRIAN_TOKEN")
            if not final_key:
                return False, "No Cambrian Token provided and none found in environment."

            async with httpx.AsyncClient(verify=False) as client:
                headers = {"Authorization": f"Bearer {final_key}"}
                response = await client.get(
                    "https://api.cambrian.pegatroncorp.com/assistant/llm_model", 
                    headers=headers, 
                    timeout=10
                )
                if response.status_code == 200:
                    models = response.json().get('llm_list', [])
                    return True, f"Connected! Found {len(models)} models."
                elif response.status_code == 401:
                    return False, "Authentication failed (401). Check your Token."
                else:
                    return False, f"Connection failed with status {response.status_code}"
        else:
            # Test OpenAI Connection (List Models)
            # Fallback to env var if key is empty
            final_key = api_key or os.getenv("OPENAI_API_KEY")
            if not final_key:
                return False, "No API Key provided and none found in environment."
                
            client = AsyncOpenAI(api_key=final_key)
            # Just try to list models to verify key
            await client.models.list()
            return True, "Connected to OpenAI successfully!"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

async def analyze_with_llm(log_evidence, openai_api_key=None, cambrian_token=None, model="gpt-4o"):
    """
    Sends the parsed log evidence to OpenAI for RCA.
    """
    # 1. Configure Client (OpenAI vs Cambrian)
    if model == "cambrian-llama-3.3-70b":
        if not cambrian_token:
             raise ValueError("Cambrian Token is required for this model")
             
        # Cambrian Integration (Internal Pegatron Gateway)
        # Allows usage of internal Llama models without external internet
        client = AsyncOpenAI(
            api_key=cambrian_token,
            base_url="https://api.cambrian.pegatroncorp.com/v1",
            http_client=httpx.AsyncClient(verify=False)
        )
        actual_model = "LLAMA 3.3 70B"
    else:
        if not openai_api_key:
             raise ValueError("OpenAI API Key is required for this model")
             
        # Standard OpenAI
        client = AsyncOpenAI(api_key=openai_api_key)
        actual_model = model
    
    system_prompt = """
    You are a Senior Android BSP (Board Support Package) Technical Expert. 
    Your specialty is debugging complex system stability issues (ANR, Crash, Watchdog, Kernel Panic) in the Android Framework, HAL (Hardware Abstraction Layer), and Kernel drivers.
    
    Goal: Analyze the provided log excerpts to identify the root cause of the failure. Focus on the interaction between the Android Framework and the underlying Hardware/Drivers.

    Structure your response in MARKDOWN format:
    1. **Executive Summary**: Concise overview (1-2 sentences).
    2. **Root Cause Analysis**: Deep technical deep-dive. 
       - Identify the blocked thread/process.
       - Trace the call stack down to the HAL/Kernel layer (e.g., waiting for `ioctl`, `binder` transaction, or hardware register).
       - Correlate timestamps between ANR traces and System/Kernel logs.
    3. **Evidence**:
       
       ### ANR Information
       - Time:
       - Process:
       - Reason:
       - Blocked Thread:

       ### Stack Trace / Logs
       > **Source**: filename.txt
       
       ```plaintext
       [Code content]
       ```
    4. **Impact**: User-facing symptoms (e.g., Keypad frozen because system_server input thread is blocked).
    5. **Recommendations**: BSP-level fixes (e.g., specific driver patches, increasing HAL timeouts, fixing race conditions in QMI/Modem).

    If logs suggest a hardware or vendor-specific issue (like Qualcomm/MediaTek), explicitly mention it.
    """
    
    user_prompt = f"""
    Please analyze the following Android system logs (ANR traces, Logcat errors):
    
    {log_evidence}
    """
    
    # Check for o1 models which may not support 'system' role or have different params
    if model.startswith("o1-"):
        # o1-preview/o1-mini currently supports 'user' and 'assistant' roles, 
        # but often performs better if system instructions are in the first user message.
        # Also, temperature is often not supported or fixed at 1.0.
        messages = [
            {"role": "user", "content": f"{system_prompt}\n\nRunning Logic:\n{user_prompt}"}
        ]
        # o1 models do not support temperature parameter in some API versions
        response = await client.chat.completions.create(
            model=actual_model, 
            messages=messages
        )
    else:
        # Standard GPT models (and Cambrian)
        # Cambrian uses standard Chat format, so it falls here
        response = await client.chat.completions.create(
            model=actual_model, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
    
    return response.choices[0].message.content
