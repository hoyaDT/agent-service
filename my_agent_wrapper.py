import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled, ModelSettings
import re

# 读取 .env 配置
load_dotenv()
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# 初始化客户端
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)

# ====== 工具函数 ======
@function_tool
def read_prompt_check_refer() -> str:
    """读取本地 prompt_check_refer.json 文件"""
    with open("prompt_check_refer.json", "r", encoding="utf-8") as f:
        return f.read()

@function_tool
def read_json_generate_refer() -> str:
    """读取本地 json_generate_refer.json 文件"""
    with open("json_generate_refer.json", "r", encoding="utf-8") as f:
        return f.read()

# ====== Agent 1：检查用户指令 ======
prompt_checker_agent = Agent(
    name="prompt_checker_agent",
    instructions=(
        "你接收用户输入的自然语言指令，并读取 prompt_check_refer.json (通过 read_prompt_check_refer)。\n"
        "根据其中定义的必填字段，逐项检查用户输入是否完整且表达清晰。\n"
        "在可以理解的情况下，尽量不要进行二轮确认。如果实在无法理解表达或缺少必填项，则告知用户需要补充什么，并等待用户补充。注意时间设置是可选项，如果没有填入也请不要二轮确认。\n"
        "当指令完整时，输出一句固定话：'指令完整'。\n"
    ),
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    model_settings=ModelSettings(temperature=0.7),
    tools=[read_prompt_check_refer],
)

# ====== Agent 2：生成 JSON ======
json_generator_agent = Agent(
    name="json_generator_agent",
    instructions=(
        "你接收用户最终确认过的完整指令，并读取 json_generate_refer.json (通过 read_json_generate_refer)。\n"
        "结合用户输入与模板内容，生成符合 json_generate_refer.json 结构的 JSON 文件。\n"
        "你必须严格只输出 JSON，不要带Markdown代码块标记，不要任何文字说明或解释。\n"
        "如果用户提出修改意见，请在现有 JSON 基础上进行最小化修改，不要改变整体结构。\n"
    ),
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    model_settings=ModelSettings(temperature=0.0),
    tools=[read_json_generate_refer],
)

# ====== 核心交互函数 ======
async def process_user_instruction(user_input: str, history: list[dict]) -> dict:
    """处理用户输入，返回结果 JSON 或补充提示"""

    # 临时追加当前输入到历史
    current_history = history + [{"role": "user", "content": user_input}]

    # ====== 辅助函数：提取 JSON ======
    def extract_json(text: str) -> str:
        """
        提取文本中的 JSON
        支持 ```json ... ``` 或 ``` ... ``` 包裹的 JSON
        """
        # 匹配 Markdown 代码块
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1)
        # 去掉前后空白
        return text.strip()
    
    # ====== 第一步：检查指令完整性 ======
    check_result = await Runner.run(prompt_checker_agent, current_history)
    check_text = check_result.final_output.strip()

    if "指令完整" in check_text:
        # ====== 第二步：生成 JSON ======
        gen_result = await Runner.run(json_generator_agent, current_history)
        raw_json = gen_result.final_output.strip()

        # 提取纯 JSON
        cleaned_json = extract_json(raw_json)

        try:
            return {"status": "success", "data": json.loads(cleaned_json)}
        except Exception:
            return {
                "status": "error",
                "message": "模型输出不是有效 JSON",
                "raw": raw_json
            }
    else:
        # 指令不完整，需要用户补充
        return {"status": "incomplete", "message": check_text}


