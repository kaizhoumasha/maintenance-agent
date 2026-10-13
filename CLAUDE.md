# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 命令

- 启动：`uv run uvicorn app.main:app --port 8000 --reload`
- 测试：`uv run pytest`（单个：`uv run pytest tests/core/test_errors.py -k name`）
- 加依赖：`uv add <pkg>`，开发依赖 `uv add --dev <pkg>`；不要手改 `uv.lock`
- 配置：`cp .env.example .env`。`MODEL_NAME` 必填，缺失时 import `app.core.config` 即报错

## 分层

`main.py`（路由）→ `services/`（业务）→ `clients/`（外部调用）。`schemas/` 放请求/响应模型，`core/` 放配置、日志、错误、trace 上下文，`middlewares/` 放中间件。依赖只能向下，路由里不写业务逻辑。各包通过 `__init__.py` 导出，跨包从包名导入（`from app.core import AppError`）。

## 约定

- **HTTP 客户端用 `httpx2`**，不是 `httpx`；异常也是 `httpx2.*`。
- **错误一律抛 `AppError(code, message, detail)`**，新错误码同时加到 `ErrorCode` 和 `HTTP_STATUS`。响应体统一为 `ErrorResponse`（含 `trace_id`），由 `core/handlers.py` 的全局 handler 生成；路由里不手写 `JSONResponse` 错误。
- `detail` 只放异常类型名或校验信息，不放上游地址等内部信息；未知异常详情只进日志。
- **trace_id** 由 `trace_id_middleware` 写入 contextvar，用 `get_trace_id()` 读取。刻意不 reset（兜底 handler 在中间件之后运行），不要“修复”。
- 阻塞调用的路由用同步 `def`（交给线程池）；改成 `async def` 前，先确认下游是异步的。
- 配置只通过 `get_settings()` / `settings` 读取，不直接读 `os.environ`。
- 类型检查用 pyright 风格；`# type: ignore` / `# pyright: ignore` 必须带原因。
- 注释、docstring、面向用户的错误消息用中文。

## 测试

- pytest，文件镜像 `app/` 结构放在 `tests/` 下。
- service 通过参数注入 `call_model_fn` 替身测试，不 patch 全局。
- 改环境变量用 `monkeypatch.setenv/delenv`。
- 新增错误码或 handler 时补 `tests/core/test_errors.py`。
