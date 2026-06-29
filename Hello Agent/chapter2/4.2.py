import os
import sys
from typing import Dict, Any, Callable
from dotenv import load_dotenv

# 设置编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

# ========================================
# 1. 搜索工具：基于 SerpApi
# ========================================
try:
    import serpapi
    
    def search(query: str) -> str:
        """
        基于 SerpApi 的网页搜索引擎工具。
        智能解析搜索结果，优先返回直接答案或知识图谱信息。
        """
        print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
        try:
            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"
            
            # 新版本 serpapi 使用 serpapi.search() 函数
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
except ImportError:
    def search(query: str) -> str:
        return "错误: 请先安装 serpapi 库 (pip install serpapi)"

# ========================================
# 2. 工具执行器：ToolExecutor 类
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
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
        
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")
    
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
# 3. 测试代码
# ========================================
if __name__ == '__main__':
    # 初始化工具执行器
    toolExecutor = ToolExecutor()
    
    # 注册搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)
    
    # 打印可用工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())
    
    # 模拟智能体调用工具
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"
    tool_function = toolExecutor.getTool(tool_name)
    
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误:未找到名为 '{tool_name}' 的工具。")