import time
import json
import redis
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from my_agent_wrapper import process_user_instruction

# ====== 初始化 FastAPI ======
app = FastAPI(title="Agent Service", version="0.2")

# ====== Redis 配置 ======
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

SESSION_EXPIRE_SECONDS = 3600  # 会话保存 1 小时

# ====== 请求与响应模型 ======
class AgentRequest(BaseModel):
    session_id: str
    input: str

class AgentResponse(BaseModel):
    status: str  # success / incomplete / error
    output: Optional[Dict[str, Any]] = None  # 成功时返回 JSON 数据
    message: Optional[str] = None  # 提示信息（incomplete 或 error）
    timing: Dict[str, float]

# ====== 健康检查接口 ======
@app.get("/health")
async def health():
    return {"status": "ok"}

# ====== 主接口 ======
@app.post("/agent", response_model=AgentResponse)
async def agent_endpoint(req: AgentRequest):
    start_time = time.perf_counter()

    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Input is empty")

    key = f"session:{req.session_id}"

    # 1. 从 Redis 获取历史
    raw_history = r.lrange(key, 0, -1)  # 最新到最旧
    history = [json.loads(item) for item in raw_history] if raw_history else []

    # 2. 调用智能体
    result = await process_user_instruction(req.input, history)

    # 3. 保存用户输入到 Redis
    r.rpush(key, json.dumps({"role": "user", "content": req.input}))

    # 4. 保存 AI 输出到 Redis
    if result.get("status") == "success":
        r.rpush(
            key,
            json.dumps({"role": "assistant", "content": json.dumps(result["data"], ensure_ascii=False)})
        )
    else:
        r.rpush(
            key,
            json.dumps({"role": "assistant", "content": result.get("message", "")})
        )

    # 5. 设置会话过期时间（1 小时）
    r.expire(key, SESSION_EXPIRE_SECONDS)

    # 6. 组装响应
    response = {
        "status": result.get("status"),
        "output": result.get("data"),
        "message": result.get("message"),
        "timing": {"total_s": time.perf_counter() - start_time}
    }
    return response
