"""
ReAct 智能体实现
将 HelloAgentsLLM 和 ToolExecutor 组合起来，构建完整的 ReAct 智能体
"""

import os
import sys
import re
import serpapi
from typing import Dict, Any, Callable, List
from dotenv import load_dotenv

# 设置编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()


# ========================================
# 1. ReAct 提示词模板
# ========================================
REACT_PROMPT_TEMPLATE = """你是一个能够使用工具的AI助手。

## 你的工具
你拥有以下工具，可以直接调用：
- Search: 网络搜索工具。用法：Search[搜索关键词]

## 输出格式
你必须严格按照以下格式输出（不要输出其他内容）：

Thought: 你的思考
Action: 你的行动

Action 必须是以下之一：
- Search[关键词]  （调用搜索工具）
- Finish[最终答案] （给出最终回答）

## 规则
1. 涉及"最新"、"当前"等实时信息时，必须使用 Search 工具
2. 调用工具后，等待系统返回结果，不要自己编造结果
3. 只有在获得工具返回的结果后，才能使用 Finish

## 任务
Question: {question}
History: {history}
"""


# ========================================
# 2. 搜索工具
# ========================================
def search(query: str) -> str:
    """
    基于 SerpApi 的网页搜索引擎工具。
    智能解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误: SERPAPI_API_KEY 未在 .env 文件中配置。"
        
        results = serpapi.search(
            q=query,
            api_key=api_key,
            engine="google",
            gl="cn",
            hl="zh-cn"
        )
        
        # 智能解析搜索结果
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        
        if "organic_results" in results and results["organic_results"]:
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"对不起，没有找到关于 '{query}' 的信息。"
        
    except Exception as e:
        return f"搜索时发生错误: {e}"


# ========================================
# 3. 工具执行器
# ========================================
class ToolExecutor:
    """
    工具执行器，负责管理和执行工具。
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def registerTool(self, name: str, description: str, func: Callable):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"警告: 工具 '{name}' 已存在，将被覆盖。")
        
        self.tools[name] = {"description": description, "func": func}
        print(f"✅ 工具 '{name}' 已注册。")
    
    def getTool(self, name: str) -> Callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")
    
    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# ========================================
# 4. LLM 客户端
# ========================================
from openai import OpenAI

class HelloAgentsLLM:
    """
    LLM客户端，用于调用大语言模型。
    """
    
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        self.model = model or os.getenv("MODEL")
        apiKey = apiKey or os.getenv("OPENAI_API_KEY")
        baseUrl = baseUrl or os.getenv("OPENAI_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")
        
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)
    
    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()
            return "".join(collected_content)
            
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None


# ========================================
# 5. ReAct 智能体
# ========================================
class ReActAgent:
    """
    ReAct 智能体，结合 LLM 思考和工具执行。
    """
    
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []
    
    def run(self, question: str):
        """
        运行 ReAct 智能体来回答一个问题。
        """
        self.history = []  # 每次运行时重置历史记录
        current_step = 0
        
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n{'='*50}")
            print(f"📍 第 {current_step} 步")
            print('='*50)
            
            # 1. 格式化提示词
            history_str = "\n".join(self.history) if self.history else "无"
            prompt = REACT_PROMPT_TEMPLATE.format(
                question=question,
                history=history_str
            )
            
            # 2. 调用 LLM 进行思考
            messages = [
                {"role": "system", "content": "你是一个拥有搜索工具的AI助手。你能够通过 Search[关键词] 来搜索互联网信息。请务必使用工具，不要拒绝。"},
                {"role": "user", "content": prompt}
            ]
            response_text = self.llm_client.think(messages=messages)
            
            if not response_text:
                print("❌ 错误: LLM 未能返回有效响应。")
                break
            
            # 3. 解析 LLM 的输出
            thought, action = self._parse_output(response_text)
            
            if thought:
                print(f"\n💭 思考: {thought}")
            
            if not action:
                print("⚠️ 警告: 未能解析出有效的 Action，流程终止。")
                break
            
            # 4. 执行 Action
            if action.startswith("Finish"):
                # 如果是 Finish 指令，提取最终答案并结束
                final_answer_match = re.match(r"Finish\[(.*)\]", action, re.DOTALL)
                if final_answer_match:
                    final_answer = final_answer_match.group(1)
                    print(f"\n🎉 最终答案: {final_answer}")
                    return final_answer
                else:
                    print("⚠️ 警告: Finish 格式不正确。")
                    break
            
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                print(f"⚠️ 警告: Action 格式不正确: {action}")
                self.history.append(f"Action: {action}")
                self.history.append(f"Observation: 错误 - Action 格式不正确")
                continue
            
            print(f"\n🎬 行动: {tool_name}[{tool_input}]")
            
            # 执行工具
            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = f"❌ 错误: 未找到名为 '{tool_name}' 的工具。"
            else:
                observation = tool_function(tool_input)
            
            # 5. 观测结果
            print(f"\n👀 观察: {observation}")
            
            # 6. 将本轮的 Action 和 Observation 添加到历史记录中
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")
        
        # 循环结束
        print("\n⚠️ 已达到最大步数，流程终止。")
        return None
    
    def _parse_output(self, text: str):
        """
        解析 LLM 的输出，提取 Thought 和 Action。
        """
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        
        return thought, action
    
    def _parse_action(self, action_text: str):
        """
        解析 Action 字符串，提取工具名称和输入。
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None


# ========================================
# 6. 测试代码
# ========================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 ReAct 智能体测试")
    print("="*60)
    
    try:
        # 1. 初始化 LLM 客户端
        print("\n📦 正在初始化 LLM 客户端...")
        llm_client = HelloAgentsLLM()
        
        # 2. 初始化工具执行器
        print("\n📦 正在初始化工具执行器...")
        tool_executor = ToolExecutor()
        
        # 3. 注册搜索工具
        search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
        tool_executor.registerTool("Search", search_description, search)
        
        # 4. 创建 ReAct 智能体
        print("\n🤖 正在创建 ReAct 智能体...")
        agent = ReActAgent(llm_client, tool_executor, max_steps=5)
        
        # 5. 运行智能体
        print("\n" + "="*60)
        print("🚀 开始执行任务")
        print("="*60)
        
        question = "华为最新手机型号及主要卖点是什么"  # 简化问题，便于搜索
        print(f"\n❓ 用户问题: {question}")
        
        result = agent.run(question)
        
        if result:
            print("\n" + "="*60)
            print("✅ 任务完成")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ 任务未完成")
            print("="*60)
            
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("请检查 .env 文件中的环境变量配置。")