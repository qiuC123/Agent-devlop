from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import traceback

load_dotenv()

def test_api_detailed():
    print("=" * 60)
    print("Detailed API Connection Test")
    print("=" * 60)
    print()
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("MODEL", "gpt-5.5")
    
    print("Configuration:")
    print("-" * 40)
    print(f"API Key: {api_key[:20]}...{api_key[-4:] if len(api_key) > 20 else 'N/A'}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
    # Test 1: Check API key format
    print("Test 1: API Key Format")
    print("-" * 40)
    if api_key and api_key.startswith("sk-"):
        print("OK - API key format looks valid (starts with 'sk-')")
    else:
        print("ERROR - API key format might be incorrect")
        print("  Expected format: 'sk-...'")
    print()
    
    # Test 2: Check base URL
    print("Test 2: Base URL")
    print("-" * 40)
    if base_url:
        print(f"Base URL: {base_url}")
        # Test if URL is reachable
        try:
            response = requests.get(base_url, timeout=5)
            print(f"OK - Base URL is reachable (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"ERROR - Cannot reach base URL: {str(e)[:100]}")
    else:
        print("ERROR - Base URL is not set")
        print("  Using default: https://api.openai.com/v1")
    print()
    
    # Test 3: Try to create OpenAI client
    print("Test 3: OpenAI Client")
    print("-" * 40)
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        print("OK - OpenAI client created successfully")
    except Exception as e:
        print(f"ERROR - Failed to create client: {str(e)}")
        return
    print()
    
    # Test 4: Try API call with timeout
    print("Test 4: API Call Test")
    print("-" * 40)
    print("Attempting to call API...")
    print("This may take a few seconds...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Reply with just 'Hello!' to confirm you're working."}
            ],
            max_tokens=20,
            timeout=30  # 30 second timeout
        )
        
        print("OK - API call successful!")
        print()
        print("Response:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)
        print()
        print("Your agent is ready to use!")
        
    except Exception as e:
        print(f"ERROR - API call failed: {str(e)}")
        print()
        print("Detailed error:")
        traceback.print_exc()
        print()
        print("Troubleshooting:")
        print("- Check if your API key is valid")
        print("- Check if the base URL is correct")
        print("- Check if the model name exists")
        print("- Check your internet connection")

if __name__ == "__main__":
    test_api_detailed()
