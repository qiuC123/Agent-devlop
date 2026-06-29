"""
Plan-and-Solve 智能体实现
将复杂问题分解为多个步骤，逐步执行并整合结果
"""

import os
import sys
import ast
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

# 设置编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()


# ========================================
# LLM 客户端
# ========================================
class HelloAgentsLLM:
    """LLM客户端，用于调用大语言模型"""
    
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        self.model = model or os.getenv("MODEL")
        apiKey = apiKey or os.getenv("OPENAI_API_KEY")
        baseUrl = baseUrl or os.getenv("OPENAI_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")
        
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)
    
    def think(self, messages: List[dict], temperature: float = 0) -> str:
        """调用大语言模型进行思考"""
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
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
# 1. 规划器提示词模板
# ========================================
PLANNER_PROMPT_TEMPLATE = """你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""


# ========================================
# 2. 执行器提示词模板
# ========================================
EXECUTOR_PROMPT_TEMPLATE = """你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""


# ========================================
# 3. 规划器
# ========================================
class Planner:
    """
    规划器：将复杂问题分解为多个简单步骤
    """
    
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
    
    def plan(self, question: str) -> List[str]:
        """
        根据用户问题生成一个行动计划。
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        
        # 构建消息列表
        messages = [{"role": "user", "content": prompt}]
        
        print("\n" + "="*50)
        print("📋 正在生成计划...")
        print("="*50)
        
        # 使用流式输出来获取完整的计划
        response_text = self.llm_client.think(messages=messages) or ""
        
        print(f"\n✅ 计划已生成:")
        print(response_text)
        
        # 解析LLM输出的列表字符串
        try:
            # 找到 ```python 和 ``` 之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用 ast.literal_eval 来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []


# ========================================
# 4. 执行器
# ========================================
class Executor:
    """
    执行器：逐步执行计划中的每个步骤
    """
    
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
    
    def execute(self, question: str, plan: List[str]) -> str:
        """
        根据计划，逐步执行并解决问题。
        """
        history = ""  # 用于存储历史步骤和结果的字符串
        
        print("\n" + "="*50)
        print("🚀 正在执行计划...")
        print("="*50)
        
        for i, step in enumerate(plan):
            print(f"\n{'─'*40}")
            print(f"📍 执行步骤 {i+1}/{len(plan)}: {step}")
            print("─"*40)
            
            # 格式化提示词
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )
            
            messages = [{"role": "user", "content": prompt}]
            
            response_text = self.llm_client.think(messages=messages) or ""
            
            # 更新历史记录，为下一步做准备
            history += f"步骤 {i+1}: {step}\n结果: {response_text}\n\n"
            
            print(f"\n✅ 步骤 {i+1} 已完成")
        
        # 循环结束后，最后一步的响应就是最终答案
        final_answer = response_text
        return final_answer


# ========================================
# 5. Plan-and-Solve 智能体
# ========================================
class PlanAndSolveAgent:
    """
    Plan-and-Solve 智能体
    先规划，后执行
    """
    
    def __init__(self, llm_client: HelloAgentsLLM):
        """
        初始化智能体，同时创建规划器和执行器实例。
        """
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)
    
    def run(self, question: str):
        """
        运行智能体的完整流程：先规划，后执行。
        """
        print("\n" + "="*60)
        print("🤖 Plan-and-Solve 智能体启动")
        print("="*60)
        print(f"\n❓ 问题: {question}")
        
        # 1. 调用规划器生成计划
        plan = self.planner.plan(question)
        
        # 检查计划是否成功生成
        if not plan:
            print("\n❌ 任务终止：无法生成有效的行动计划。")
            return None
        
        print(f"\n📋 计划共 {len(plan)} 个步骤:")
        for i, step in enumerate(plan, 1):
            print(f"   {i}. {step}")
        
        # 2. 调用执行器执行计划
        final_answer = self.executor.execute(question, plan)
        
        print("\n" + "="*60)
        print("🎉 任务完成")
        print("="*60)
        print(f"\n📝 最终答案: {final_answer}")
        
        return final_answer


# ========================================
# 6. 测试代码
# ========================================
if __name__ == '__main__':
    try:
        # 初始化 LLM 客户端
        llm_client = HelloAgentsLLM()
        
        # 创建 Plan-and-Solve 智能体
        agent = PlanAndSolveAgent(llm_client)
        
        # 测试问题
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        
        # 运行智能体
        result = agent.run(question)
        
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("请检查 .env 文件中的环境变量配置。")