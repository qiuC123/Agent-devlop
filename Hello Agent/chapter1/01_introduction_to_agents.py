class SimpleAgent:
    def __init__(self, name, role, instructions):
        self.name = name
        self.role = role
        self.instructions = instructions
        self.memory = []
    
    def think(self, input_message):
        self.memory.append({"input": input_message})
        return f"Si kao zhong: {input_message}"
    
    def act(self, thought):
        action = f"Zhi xing xing dong: Gen ju si kao '{thought}' cai qu xing dong"
        self.memory.append({"action": action})
        return action
    
    def observe(self, result):
        observation = f"Guan cha jie guo: {result}"
        self.memory.append({"observation": observation})
        return observation

def main():
    print("=" * 60)
    print("Chapter 1: Introduction to Agents")
    print("=" * 60)
    print()
    print("1. What is an Agent?")
    print("-" * 40)
    print("An agent is an entity that can perceive the environment, make decisions, and take actions.")
    print("It has the following core characteristics:")
    print("  - Perception: Obtain environmental information")
    print("  - Decision: Make judgments based on information")
    print("  - Action: Execute specific operations")
    print("  - Learning: Improve from experience")
    print()
    
    print("2. Classic Agent Paradigms")
    print("-" * 40)
    paradigms = [
        {
            "name": "ReAct",
            "description": "Reasoning + Acting, reason first then act",
            "flow": "Think -> Act -> Observe -> Loop"
        },
        {
            "name": "Plan-and-Solve",
            "description": "Plan first then execute",
            "flow": "Analyze -> Plan -> Execute step by step"
        },
        {
            "name": "Reflection",
            "description": "Self-reflection, learn from failures",
            "flow": "Execute -> Reflect -> Improve -> Re-execute"
        }
    ]
    
    for p in paradigms:
        print(f"\n  {p['name']}:")
        print(f"    Description: {p['description']}")
        print(f"    Flow: {p['flow']}")
    
    print()
    print("3. Create a Simple Agent")
    print("-" * 40)
    
    agent = SimpleAgent(
        name="Learning Assistant",
        role="Help users learn agent development",
        instructions="You are a friendly learning assistant, helping users understand agent concepts"
    )
    
    print(f"  Agent Name: {agent.name}")
    print(f"  Agent Role: {agent.role}")
    print(f"  Instructions: {agent.instructions}")
    
    print()
    print("4. Agent Execution Flow Example (ReAct Paradigm)")
    print("-" * 40)
    
    user_input = "What is the ReAct paradigm?"
    
    thought = agent.think(user_input)
    print(f"\n  [Think] {thought}")
    
    action = agent.act(thought)
    print(f"  [Act] {action}")
    
    observation = agent.observe("User wants to understand the ReAct paradigm")
    print(f"  [Observe] {observation}")
    
    print()
    print("5. Agent Application Scenarios")
    print("-" * 40)
    applications = [
        "Smart Search Assistant",
        "Automated Office Assistant",
        "Smart Travel Planner",
        "Code Generation and Debugging",
        "Scientific Research Assistant",
        "Smart Home Control",
        "Game NPC",
        "Business Analysis Consultant"
    ]
    
    for app in applications:
        print(f"  - {app}")
    
    print()
    print("=" * 60)
    print("Chapter 1 Learning Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()