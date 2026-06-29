from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class HelloAgent:
    def __init__(self, model=None):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = model or os.getenv("MODEL", "gpt-5.5")
        self.messages = []
    
    def set_system_prompt(self, prompt):
        self.messages = [{"role": "system", "content": prompt}]
    
    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_history(self):
        self.messages = []

def main():
    print("=" * 60)
    print("Hello Agent - First Agent Program")
    print("=" * 60)
    print()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Warning: OPENAI_API_KEY is not set")
        print("Please set your API Key in the .env file")
        print()
        print("Example .env file content:")
        print("OPENAI_API_KEY=your-api-key-here")
        print("OPENAI_BASE_URL=https://api.openai.com/v1")
        print("MODEL=gpt-5.5")
        print()
        return
    
    model_name = os.getenv("MODEL", "gpt-5.5")
    print(f"Using model: {model_name}")
    print()
    
    agent = HelloAgent()
    
    agent.set_system_prompt("You are a friendly AI assistant that helps users learn agent development. Please answer questions concisely and clearly.")
    
    print("Agent is ready! Type 'exit' or 'quit' to exit.")
    print()
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit"]:
            print("Agent: Goodbye! Welcome to learn again next time!")
            break
        
        if not user_input.strip():
            print("Agent: Please enter a question or message.")
            continue
        
        print("Agent: Thinking...")
        response = agent.chat(user_input)
        print(f"Agent: {response}")
        print()

if __name__ == "__main__":
    main()