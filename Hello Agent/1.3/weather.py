"""
1.3 章节：构建一个真实的智能体
一个由LLM驱动的智能旅行助手，能够查询天气并推荐景点
"""

import os
import re
import requests
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# 加载环境变量
load_dotenv()

# ============================================================================
# (1) 指令模板 - System Prompt
# ============================================================================
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""

# ============================================================================
# (2) 工具 1：查询真实天气
# ============================================================================
def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    # API端点，我们请求JSON格式的数据
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()
        
        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        
        # 格式化成自然语言返回
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    
    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误:查询天气时遇到网络问题 - {e}"
    
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"

# ============================================================================
# (3) 工具 2：搜索并推荐旅游景点
# ============================================================================
def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    # 1. 从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"
    
    # 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)
    
    # 3. 构造一个精确的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"
    
    try:
        # 4. 调用API，include_answer=True会返回一个综合性的回答
        response = tavily.search(
            query=query, 
            search_depth="basic",
            include_answer=True
        )
        
        # 5. Tavily返回的结果已经非常干净，可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]
        
        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        
        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"
        
        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"

# ============================================================================
# 工具字典
# ============================================================================
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

# ============================================================================
# (4) OpenAI兼容客户端
# ============================================================================
class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"

# ============================================================================
# (5) 执行行动循环 - 主程序
# ============================================================================
def run_agent(user_prompt: str, max_loops: int = 5):
    """
    运行智能体主循环
    """
    # --- 1. 配置LLM客户端 ---
    API_KEY = os.environ.get("OPENAI_API_KEY")
    BASE_URL = os.environ.get("OPENAI_BASE_URL")
    MODEL_ID = os.environ.get("MODEL", "gpt-5.5")
    
    if not API_KEY:
        print("错误: 未配置 OPENAI_API_KEY")
        return
    
    llm = OpenAICompatibleClient(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    # --- 2. 初始化 ---
    prompt_history = [f"用户请求: {user_prompt}"]
    print(f"用户输入: {user_prompt}\n" + "=" * 40)
    
    # --- 3. 运行主循环 ---
    for i in range(max_loops):
        print(f"\n--- 循环 {i+1} ---\n")
        
        # 3.1. 构建Prompt
        full_prompt = "\n".join(prompt_history)
        
        # 3.2. 调用LLM进行思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        
        # 模型可能会输出多余的Thought-Action，需要截断
        match = re.search(
            r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', 
            llm_output, 
            re.DOTALL
        )
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print("已截断多余的 Thought-Action 对")
        
        print(f"LLM输出:\n{llm_output}\n")
        
        # 3.3. 记录LLM的思考过程
        prompt_history.append(llm_output)
        
        # 3.4. 解析Action
        action_match = re.search(r'Action:\s*(.+)', llm_output)
        if not action_match:
            print("无法解析Action，继续下一轮...")
            continue
        
        action_text = action_match.group(1).strip()
        
        # 3.5. 检查是否结束
        finish_match = re.search(r'Finish\[(.+)\]', action_text)
        if finish_match:
            final_answer = finish_match.group(1)
            print("\n" + "=" * 40)
            print(f"最终答案: {final_answer}")
            print("=" * 40)
            break
        
        # 3.6. 解析并执行工具调用
        # 格式: function_name(arg_name="arg_value")
        tool_match = re.search(r'(\w+)\(([^)]+)\)', action_text)
        if tool_match:
            tool_name = tool_match.group(1)
            args_str = tool_match.group(2)
            
            # 解析参数
            args = {}
            # 解析带引号的参数: city="北京"
            for name, value in re.findall(r'(\w+)="([^"]*)"', args_str):
                args[name] = value
            # 解析不带引号的参数: city=北京
            for name, value in re.findall(r'(\w+)=([^",\s]+)', args_str):
                if name not in args:
                    args[name] = value
            
            # 执行工具
            if tool_name in available_tools:
                print(f"执行工具: {tool_name}，参数: {args}")
                try:
                    observation = available_tools[tool_name](**args)
                except Exception as e:
                    observation = f"工具执行错误: {e}"
                print(f"观察结果: {observation}\n")
                prompt_history.append(f"Observation: {observation}")
            else:
                print(f"未知工具: {tool_name}")
                prompt_history.append(f"Observation: 错误: 工具'{tool_name}'不存在")
        else:
            print(f"无法解析工具调用: {action_text}")
            prompt_history.append(f"Observation: 错误: 无法解析行动'{action_text}'")
    
    if i == max_loops - 1:
        print("\n达到最大循环次数，任务可能未完成。")

# ============================================================================
# 主程序入口
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("智能旅行助手 - 1.3 章节示例")
    print("=" * 60)
    print()
    
    # 检查API配置
    print("检查API配置...")
    print(f"OPENAI_API_KEY: {'已配置' if os.environ.get('OPENAI_API_KEY') else '未配置'}")
    print(f"TAVILY_API_KEY: {'已配置' if os.environ.get('TAVILY_API_KEY') else '未配置'}")
    print(f"MODEL: {os.environ.get('MODEL', 'gpt-5.5')}")
    print()
    
    # 运行智能体
    user_prompt = "你好，请帮我查询一下今天江苏的天气，然后根据天气推荐一个合适的旅游景点。"
    run_agent(user_prompt)