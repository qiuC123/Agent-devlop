from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def test_api():
    print("=" * 60)
    print("API Connection Test")
    print("=" * 60)
    print()
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("MODEL", "gpt-5.5")
    
    print(f"API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
    print("Testing connection...")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello and confirm you are working!"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("Success! API is working correctly.")
        print()
        print("Response from AI:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)
        print()
        print("You can now run the interactive agent!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()
        print("Please check your API key and base URL.")

if __name__ == "__main__":
    test_api()