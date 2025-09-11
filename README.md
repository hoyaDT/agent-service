# Agent Service

## 1. 项目简介

`Agent Service` 是一个基于 **FastAPI + OpenAI Agents SDK + DeepSeek API** 的智能体服务。
它可以接收自然语言指令，检查指令完整性，并生成对应的 JSON 配置供后续自动化流程使用。


## 2. 文件结构

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

## 3. 环境配置（可选开发方式）

> 如果你只想快速在本地调试，可以使用 Python 虚拟环境运行。
> **推荐在 Docker 中运行以保证环境一致性。**

1. **Python 版本**：推荐 3.11
2. **虚拟环境安装依赖（可选）**：

```bash
# 激活虚拟环境
# Linux / Mac
source .venv/bin/activate
# Windows（PowerShell）
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

---

## 4. Docker 启动方式（推荐）

1. **使用 Docker Compose 启动**：

```bash
docker-compose up --build -d
```

2. **容器启动后**，服务会监听 **8000 端口**，接口可通过：

   * Swagger UI：`http://<host>:8000/docs`
   * ReDoc：`http://<host>:8000/redoc`

> Docker Compose 会自动构建镜像和启动服务，无需手动 build/run。


---

## 5. FastAPI 接口

### 5.1 健康检查

```http
GET /health
```

**返回示例**：

```json
{
  "status": "ok"
}
```

### 5.2 主接口：发送指令

```http
POST /agent
Content-Type: application/json

{
  "session_id": "string",
  "input": "string"
}
```

**返回示例**：

```json
{
  "status": "success",
  "output": {
    "instruction": "K405",
    "telemetry": [
      {
        "code": "PKOSV2AS5_TMAS05001",
        "criteria": "equals",
        "value": 5
      },
      {
        "code": "PKOSV2AS5_TMAS05002",
        "criteria": "equals",
        "value": 5
      }
    ],
    "logic": "and"
  },
  "message": null,
  "timing": {
    "total_s": 3.3142233459993804
  }
}
```

* `status` 可为：

  * `"success"`：生成了可用 JSON
  * `"incomplete"`：指令不完整，需要二轮交互
  * `"error"`：模型输出异常


---

## 6. Swagger 文档（交互式 API）

* FastAPI 自带 Swagger UI 和 ReDoc
* **Swagger UI**：`http://<host>:8000/docs`
* **ReDoc**：`http://<host>:8000/redoc`
* 可以直接访问，看到接口参数和返回示例

---

