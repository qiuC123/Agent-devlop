# ============================================================================
# Python 初学者指南：智能体开发入门
# ============================================================================

"""
===============================================================================
第一章：Python 基础回顾
===============================================================================

在我们开始学习智能体之前，先回顾一些 Python 的基础知识：

1. 变量和数据类型
   name = "北京"        # 字符串（文字）
   temperature = 25     # 整数（数字）
   is_hot = True        # 布尔值（真/假）
   items = ["天气", "景点"]  # 列表（一组数据）

2. 函数 - 就像一个小型加工机器
   def 加工原材料(原材料):
       处理过程...
       return 成品

3. 类 - 像一个模板或蓝图
   class 机器人:
       def __init__(self, 名字):
           self.名字 = 名字
       
       def 说话(self):
           print("你好！")

4. 导入模块 - 使用别人写好的代码
   import os           # 操作系统相关的功能
   import requests     # 发送网络请求
"""

# ============================================================================
# 第二章：代码详解
# ============================================================================

"""
===============================================================================
2.1 导入必要的库
===============================================================================

import os          # 用于读取环境变量（比如API密钥）
import re          # 用于匹配和查找文字（正则表达式）
import requests    # 用于发送网络请求，获取网页数据
from dotenv import load_dotenv  # 从.env文件加载配置
from openai import OpenAI       # OpenAI官方SDK
from tavily import TavilyClient  # Tavily搜索API客户端
"""

# 实际代码：
import os
import re
import requests
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# 加载环境变量（非常重要！）
load_dotenv()
print("[OK] 环境变量加载成功")
print("  - OPENAI_API_KEY:", "已配置" if os.getenv("OPENAI_API_KEY") else "未配置")
print("  - TAVILY_API_KEY:", "已配置" if os.getenv("TAVILY_API_KEY") else "未配置")

"""
===============================================================================
小知识：什么是环境变量？
===============================================================================

想象你有一些秘密的东西（比如密码），你不应该把它们直接写在代码里，
因为：
1. 别人能看到你的代码，就会知道你的密码
2. 如果你要换密码，需要修改代码
3. 不小心上传到GitHub，全世界都能看到

环境变量就像是一个"秘密盒子"：
- 你把秘密放在 .env 文件中
- 代码从这个盒子里读取秘密
- 这样代码里就不会出现真正的密码了

.env 文件示例：
OPENAI_API_KEY=sk-xxxxxxx
TAVILY_API_KEY=tvly-xxxxxxx
"""

# ============================================================================
# 第三章：指令模板（System Prompt）
# ============================================================================

"""
===============================================================================
3.1 什么是 System Prompt？
===============================================================================

System Prompt 就像是给 AI 的"说明书"或"行为规范"。

想象你雇佣了一个助手：
- 你会告诉他："你是一个旅行顾问，要帮助用户规划行程"
- 你会告诉他有哪些工具可以用："你有地图、天气预报、景点资料"
- 你会告诉他工作方式："每次思考后，要先说出来，再执行"

在代码中，这个"说明书"就是一个字符串（text），我们叫它 SYSTEM_PROMPT。
"""

# 实际代码：
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
"""

print("\n" + "="*60)
print("System Prompt 说明")
print("="*60)
print("""
这个提示词告诉 AI：
1. 角色：你是智能旅行助手
2. 能力：可以查询天气、搜索景点
3. 工作方式：必须按照 Thought → Action 的格式输出
4. 思考流程：先想后做，收集足够信息后给出答案
""")

"""
===============================================================================
第四章：第一个工具 - 查询天气
===============================================================================

4.1 什么是函数？
===============================================================================

函数就像是一个有特定功能的小机器：
- 你给它输入（参数）
- 它帮你完成工作
- 它给你输出（返回值）

语法：
def 函数名(参数1, 参数2):
    '''说明文档'''
    # 做一些事情
    return 结果
"""

# 实际代码：
def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    
    参数：
        city: 城市名称，比如 "北京"、"上海"
    返回：
        天气描述字符串，比如 "北京当前天气:晴天，气温25摄氏度"
    """
    # 构建请求URL
    # f-string: 允许你在字符串中插入变量
    # {city} 会被替换成实际的城市名
    url = f"https://wttr.in/{city}?format=j1"
    
    print(f"  正在查询 {city} 的天气...")
    
    try:
        # requests.get() 发送网络请求获取数据
        response = requests.get(url)
        
        # 检查请求是否成功
        response.raise_for_status()
        
        # 将返回的JSON数据转换为Python字典
        data = response.json()
        
        # 提取天气信息
        # 想象 data 是这样的结构：
        # {
        #     "current_condition": [
        #         {
        #             "weatherDesc": [{"value": "晴天"}],
        #             "temp_C": "25"
        #         }
        #     ]
        # }
        
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        
        # 返回格式化后的字符串
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"

"""
===============================================================================
4.2 异常处理（try...except）
===============================================================================

代码可能出错，比如：
- 网络断了
- 服务器不响应
- 数据格式不对

try...except 就像"保险"：
try:
    # 尝试做这件事
    result = 可能有问题的代码
except 错误类型:
    # 如果出错了，做这个
    result = "出错了"
"""

print("\n" + "="*60)
print("测试天气查询功能")
print("="*60)

# 测试一下
weather_result = get_weather("北京")
print(f"查询结果: {weather_result}")

# ============================================================================
# 第五章：第二个工具 - 搜索景点
# ============================================================================

"""
===============================================================================
5.1 API 调用流程
===============================================================================

使用第三方服务（如Tavily搜索）的步骤：

1. 获取API密钥（就像用户名密码）
2. 安装SDK（别人写好的工具包）
3. 初始化客户端
4. 调用服务
5. 处理结果
"""

def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气搜索景点推荐
    """
    # 1. 获取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"
    
    # 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)
    
    # 3. 构造搜索查询
    # 想象你在搜索引擎里输入什么
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"
    
    try:
        # 4. 执行搜索
        response = tavily.search(
            query=query,
            search_depth="basic",
            include_answer=True  # 获取综合回答
        )
        
        # 5. 处理结果
        if response.get("answer"):
            return response["answer"]
        
        # 如果没有综合回答，格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        
        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"
        
        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"

print("\n" + "="*60)
print("工具定义完成")
print("="*60)
print("""
现在我们有两个工具了：
1. get_weather(city)    - 查询天气
2. get_attraction(city, weather) - 搜索景点

把它们放进一个字典，方便后续调用
""")

# 工具字典
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

# ============================================================================
# 第六章：OpenAI 兼容客户端
# ============================================================================

"""
===============================================================================
6.1 什么是类（Class）？
===============================================================================

类就像是一个"模板"或"蓝图"：
- 它定义了某种东西应该有什么属性（数据）
- 它定义了这种东西能做什么（方法）

举个例子：
类：汽车蓝图
- 属性：颜色、品牌、速度
- 方法：启动、加速、刹车

实例：具体的一辆车（根据蓝图造出来的）
- 这辆车的颜色是红色，品牌是宝马，当前速度是0
"""

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    
    就像一个"翻译官"：
    - 你告诉它你要问什么问题
    - 它帮你联系AI服务
    - 它把AI的回答传回来
    """
    
    def __init__(self, model: str, api_key: str, base_url: str):
        """
        初始化客户端
        
        参数：
            model: 模型名称，比如 "gpt-5.5"
            api_key: API密钥
            base_url: API地址
        """
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        print(f"[OK] LLM客户端初始化完成，使用模型: {model}")
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        调用LLM生成回答
        
        参数：
            prompt: 用户的问题
            system_prompt: 系统提示词（行为规范）
        
        返回：
            AI的回答
        """
        print("  正在调用大语言模型...")
        
        try:
            # 构建消息列表
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            # 提取回答
            answer = response.choices[0].message.content
            
            print("[OK] 大语言模型响应成功")
            return answer
        
        except Exception as e:
            print(f"[ERROR] 调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"

print("\n" + "="*60)
print("创建 LLM 客户端")
print("="*60)

# 创建客户端实例
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_ID = os.getenv("MODEL", "gpt-5.5")

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# ============================================================================
# 第七章：正则表达式基础
# ============================================================================

"""
===============================================================================
7.1 什么是正则表达式？
===============================================================================

正则表达式是一种"匹配文字"的工具。

比如：
- r'Thought: (.*?)'  可以找到"Thought: 后面到下一个部分之前的所有内容"
- r'Action: (.*)'    可以找到"Action: 后面的所有内容"

(.*?) 意思是：匹配任意字符（非贪婪）
(.*)   意思是：匹配任意字符（贪婪）

简单的比喻：
- 'Thought: xxx' 就像 '名字: 张三'
- 正则表达式就是用来找到冒号后面的内容
"""

print("\n" + "="*60)
print("正则表达式示例")
print("="*60)

# 假设AI返回了这样的文字：
sample_output = """
Thought: 用户想知道北京的天气。我需要先查询天气。
Action: get_weather(city="北京")

Observation: 北京当前天气:晴天，气温25摄氏度

Thought: 已经获取到天气信息，现在可以根据天气推荐景点了。
Action: Finish[北京今天晴天，气温25度，适合去故宫、颐和园等户外景点。]
"""

# 使用正则表达式提取信息
thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', sample_output, re.DOTALL)
if thought_match:
    print(f"找到的思考: {thought_match.group(1).strip()}")

action_match = re.search(r'Action:\s*(.+?)(?=\n|$)', sample_output)
if action_match:
    print(f"找到的行动: {action_match.group(1).strip()}")

# ============================================================================
# 第八章：主循环
# ============================================================================

"""
===============================================================================
8.1 什么是智能体的"思考-行动-观察"循环？
===============================================================================

这就像你解决问题的方式：

1. 思考：我需要做什么？下一步该什么？
2. 行动：执行计划（比如查资料、打电话）
3. 观察：看看结果怎么样
4. 重复：基于观察结果，继续思考下一步

智能体就是这样工作的：
"""

def run_agent(user_prompt: str, max_loops: int = 3):
    """
    运行智能体主循环
    
    参数：
        user_prompt: 用户的问题
        max_loops: 最大循环次数（防止无限循环）
    """
    print("\n" + "="*60)
    print("启动智能体")
    print("="*60)
    print(f"用户请求: {user_prompt}\n")
    
    # 初始化对话历史
    prompt_history = [f"用户请求: {user_prompt}"]
    
    # 主循环
    for i in range(max_loops):
        print(f"\n--- 循环 {i+1} ---\n")
        
        # 步骤1：构建完整的提示
        full_prompt = "\n".join(prompt_history)
        
        # 步骤2：调用LLM思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        
        print(f"LLM思考:\n{llm_output}\n")
        
        # 记录思考过程
        prompt_history.append(llm_output)
        
        # 步骤3：解析行动
        action_match = re.search(r'Action:\s*(.+)', llm_output)
        if not action_match:
            print("无法解析行动，尝试继续...")
            continue
        
        action_text = action_match.group(1).strip()
        
        # 步骤4：检查是否完成
        finish_match = re.search(r'Finish\[(.+)\]', action_text)
        if finish_match:
            final_answer = finish_match.group(1)
            print("\n" + "="*60)
            print("[OK] 任务完成！")
            print(f"最终答案: {final_answer}")
            print("="*60)
            return
        
        # 步骤5：执行工具
        tool_match = re.search(r'(\w+)\(([^)]+)\)', action_text)
        if tool_match:
            tool_name = tool_match.group(1)
            args_str = tool_match.group(2)
            
            # 解析参数
            args = {}
            for name, value in re.findall(r'(\w+)="([^"]*)"', args_str):
                args[name] = value
            
            # 执行工具
            if tool_name in available_tools:
                print(f"执行工具: {tool_name}")
                print(f"参数: {args}")
                
                try:
                    observation = available_tools[tool_name](**args)
                except Exception as e:
                    observation = f"工具执行错误: {e}"
                
                print(f"观察结果: {observation}\n")
                prompt_history.append(f"Observation: {observation}")
            else:
                print(f"未知工具: {tool_name}")
    
    print("\n达到最大循环次数，任务可能未完成。")

# ============================================================================
# 第九章：运行智能体
# ============================================================================

if __name__ == "__main__":
    """
    主程序入口
    
    __name__ == "__main__" 的意思是：
    "这个程序是被直接运行的，而不是被其他程序导入的"
    
    作用：
    - 如果直接运行这个文件，__name__ 是 "__main__"，会执行这段代码
    - 如果只是导入这个文件，__name__ 是文件名，不会执行这段代码
    """
    
    print("="*60)
    print("智能旅行助手")
    print("="*60)
    
    # 检查配置
    print("\n检查API配置...")
    print(f"  OPENAI_API_KEY: {'[OK]' if os.getenv('OPENAI_API_KEY') else '[MISSING]'}")
    print(f"  TAVILY_API_KEY: {'[OK]' if os.getenv('TAVILY_API_KEY') else '[MISSING]'}")
    print(f"  MODEL: {os.getenv('MODEL', 'gpt-5.5')}")
    
    # 运行智能体
    user_prompt = "你好，请帮我查询一下北京今天的天气。"
    run_agent(user_prompt, max_loops=2)

# ============================================================================
# 第十章：知识点总结
# ============================================================================

"""
===============================================================================
学习总结
===============================================================================

1. 【导入模块】
   import xxx 或 from xxx import yyy
   相当于"借用具"：使用别人写好的代码

2. 【环境变量】
   os.getenv("xxx")
   读取秘密配置（比如API密钥）

3. 【函数定义】
   def 函数名(参数) -> 返回类型:
       # 文档说明
       代码
       return 结果
   相当于"加工机器"：输入 → 加工 → 输出

4. 【类定义】
   class 类名:
       def __init__(self, 参数):
           初始化
       
       def 方法名(self, 参数):
           执行操作
   相当于"蓝图"：定义对象有什么、能做什么

5. 【API调用】
   发送请求 → 获取响应 → 解析数据
   相当于"打电话"：问问题 → 等回答 → 处理答案

6. 【正则表达式】
   re.search(模式, 文本)
   相当于"文字搜索引擎"：从文本中找特定格式的内容

7. 【异常处理】
   try:
       可能出错的操作
   except 错误类型:
       处理错误
   相当于"保险"：预防万一

8. 【思考-行动循环】
   Thought → Action → Observation
   相当于"边做边想"：做一点，想一想，再做一点

===============================================================================
下一步学习建议
===============================================================================

1. 理解这个代码的流程
2. 尝试修改代码（比如添加新工具）
3. 学习更高级的框架（LangChain、AgentScope）
4. 阅读更多智能体相关的论文和项目

加油！你已经开始学习智能体开发了！
===============================================================================
"""
