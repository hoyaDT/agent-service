# Agent Service

## 1. Quick Start

### 1.1 克隆项目代码

```bash
git clone <repo-url>
cd agent-service
```

### 1.2 确保 Docker 已启动
打开 Docker Desktop

### 1.3 构建并启动容器

```bash
docker compose up --build -d
```
这一步会自动构建镜像并启动 agent-service 和 my-redis 两个容器。

查看容器状态：
```bash
docker ps
```

### 1.4 访问接口文档

**容器启动后**，服务会监听 **8000 端口**，接口可通过：

   * Swagger UI：`http://<host>:8000/docs` （在本机访问即为`http://127.0.0.1:8000/docs`）
   * ReDoc：`http://<host>:8000/redoc` （在本机访问即为`http://127.0.0.1:8000/docs`）


---

## 2. 项目简介

`Agent Service` 是一个基于 **FastAPI + OpenAI Agents SDK + DeepSeek API** 的智能体服务。
它可以接收自然语言指令，检查指令完整性，并生成对应的 JSON 配置供后续自动化流程使用。


## 3. 文件结构

agent-service/
├─ .venv                     # Python 虚拟环境
├─ main.py                   # FastAPI 主程序
├─ my_agent_wrapper.py       # 智能体核心逻辑
├─ requirements.txt          # 项目核心必需依赖
├─ requirements-dev.txt      # 项目完整依赖
├─ .env                      # 环境变量（API Key 等）
├─ Dockerfile                # Docker 配置
├─ docker-compose.yml        # Docker Compose 配置
├─ prompt_check_refer.json   # 指令检查参考文档
├─ json_generate_refer.json  # JSON 生成参考文档
└─ README.md


---

## 4. FastAPI 接口

### 4.1 健康检查

```http
GET /health
```

**返回示例**：

```json
{
  "status": "ok"
}
```

### 4.2 主接口：发送指令

```http
POST /agent
Content-Type: application/json

{
  "session_id": "string",
  "input": "string"
}
```

**请求示例**：

```json
{
  "session_id": "001",
  "input": "在发送 K409 指令后，判断遥测代号 PKOSV2AS5_TMAS05003 或 PKOSV2AS5_TMAS05004 的遥测数据，只要其中一个在 28 到 33 之间即可。"
}
```

**返回示例**：

```json
{
  "status": "success",
  "output": {
    "code": "K409",
    "associatedTelemetry": [
      {
        "groupInfo": "PKOSV2AS5_TMAS05003",
        "criterionInStr": "[28,33]"
      },
      {
        "groupInfo": "PKOSV2AS5_TMAS05004",
        "criterionInStr": "[28,33]"
      }
    ],
    "logicalRelationAmongTelemetry": "or"
  },
  "message": null,
  "timing": {
    "total_s": 5.154623751000003
  }
}
```

### **参数说明（请求 & 返回）**

**请求参数**：  
- `session_id`：会话 ID，用于区分不同对话。只要使用相同的 `session_id`，服务会从 Redis 中读取该会话的上下文，实现连续对话的记忆功能。  
- `input`：用户输入的自然语言指令。  

**返回参数**：  
- `status`：表示指令处理结果，可为：  
  - `"success"`：生成了可用 JSON  
  - `"incomplete"`：指令不完整，需要二轮交互  
  - `"error"`：模型输出异常  
- `output`：模型生成的 JSON 输出 
- `message`：错误或提示信息，当 `status` 为 `"success"` 时为 `null`，当 `status` 为 `"error"` 或 `"incomplete"` 时会返回对应说明。
- `timing`：运行时间统计，单位为秒  
  - `total_s`：本次请求模型处理所消耗的总时间

  
---


