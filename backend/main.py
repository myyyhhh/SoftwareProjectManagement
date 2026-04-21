import json
from typing import AsyncIterator, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Header
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware

from graph import app as agent_workflow
from utils import SUPPORTED_FILE_EXTENSIONS, build_source_material, extract_text_from_file
from auth import (
    router as auth_router,
    get_current_user_id,
    create_conversation,
    add_message,
)

app = FastAPI(title="Brand-Consistent Content Agent API")
app.include_router(auth_router)  # 挂载认证路由

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _init_state(source_material: str, content_type: str, user_prompt: str = "") -> dict:
    return {
        "source_material": source_material,
        "product_spec": "",
        "content_type": content_type,
        "user_prompt": user_prompt or "",
        "messages": [],
        "is_review_approved": False,
        "is_fact_checked": False,
        "final_data": {},
        "status_updates": [],
    }


def _validate_upload(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="上传文件缺少文件名")

    lower_name = file.filename.lower()
    if not any(lower_name.endswith(ext) for ext in SUPPORTED_FILE_EXTENSIONS):
        allow = ", ".join(sorted(SUPPORTED_FILE_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"仅支持以下文件格式：{allow}")


def _prepare_source_material(
    file_bytes: Optional[bytes],
    filename: Optional[str],
    source_url: str,
    raw_text: str,
) -> str:
    file_text = ""
    if file_bytes and filename:
        file_text = extract_text_from_file(file_bytes, filename)

    return build_source_material(
        file_text=file_text,
        source_url=source_url,
        raw_text=raw_text,
    )


def run_content_generation_agent(
    source_material: str,
    content_type: str,
    user_prompt: str = "",
) -> dict:
    initial_state = _init_state(
        source_material=source_material,
        content_type=content_type,
        user_prompt=user_prompt,
    )
    try:
        result = agent_workflow.invoke(initial_state, {"recursion_limit": 14})
        return {
            "final_data": result.get("final_data", {}),
            "product_spec": result.get("product_spec", ""),
            "status_updates": result.get("status_updates", []),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"大模型内容生成失败: {str(e)}")


async def stream_content_generation_agent(
    source_material: str,
    content_type: str,
    user_prompt: str = "",
) -> AsyncIterator[str]:
    initial_state = _init_state(
        source_material=source_material,
        content_type=content_type,
        user_prompt=user_prompt,
    )

    try:
        async for chunk in agent_workflow.astream(initial_state, stream_mode="updates"):
            # chunk 形如：{"node_name": {"status_updates": [...], ...}}
            for node_name, payload in chunk.items():
                status_updates = payload.get("status_updates", []) if isinstance(payload, dict) else []
                for status in status_updates:
                    yield f"data: {json.dumps({'event': 'status', 'node': node_name, 'message': status}, ensure_ascii=False)}\n\n"

                if isinstance(payload, dict) and payload.get("final_data"):
                    yield f"data: {json.dumps({'event': 'result', 'node': node_name, 'data': payload['final_data']}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'event': 'done'}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"



@app.post("/generate_from_file")
async def generate_content_from_file(
    content_type: str = Form(..., description="要生成的内容类型，例如 blog / video / case_study"),
    file: UploadFile | None = File(None, description="可选：上传 PDF / Word / 图片文件"),
    source_url: str = Form("", description="可选：产品网页 URL"),
    raw_text: str = Form("", description="可选：直接粘贴的产品资料文本"),
    user_prompt: str = Form("", description="可选：品牌约束、口吻要求、禁用词、额外提示词"),
    conversation_id: Optional[int] = Form(None, description="可选：继续已有会话"),
    user_id: int = Depends(get_current_user_id)  # 从 token 获取用户 ID
):
    try:
        file_bytes = None
        filename = None

        if file is not None:
            _validate_upload(file)
            file_bytes = await file.read()
            filename = file.filename
            if not file_bytes:
                raise HTTPException(status_code=400, detail="上传文件为空")

        source_material = _prepare_source_material(
            file_bytes=file_bytes,
            filename=filename,
            source_url=source_url,
            raw_text=raw_text,
        )

        if conversation_id is None:
            conv_id = create_conversation(user_id, title=f"{content_type} - {filename or '文本输入'}")
        else:
            conv_id = conversation_id  # 实际应校验该会话是否属于该用户，此处略

        # 存储用户输入的提示词（作为 user 消息）
        user_input_summary = f"生成类型: {content_type}\n额外提示: {user_prompt}" if user_prompt else f"生成类型: {content_type}"
        add_message(conv_id, "user", user_input_summary)

        result = run_content_generation_agent(
            source_material=source_material,
            content_type=content_type,
            user_prompt=user_prompt,
        )

        assistant_content = json.dumps(result["final_data"], ensure_ascii=False, indent=2)
        add_message(conv_id, "assistant", assistant_content)

        return {
            "status": "success",
            "conversation_id": conv_id,
            "content_type": content_type,
            "filename": filename,
            "source_url": source_url or None,
            "data": result["final_data"],
            "product_spec": result["product_spec"],
            "trace": result["status_updates"],
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception:
        raise HTTPException(status_code=500, detail="服务器内部发生了意外错误。")


@app.post("/generate_stream")
async def generate_content_stream(
    content_type: str = Form(...),
    file: UploadFile | None = File(None),
    source_url: str = Form(""),
    raw_text: str = Form(""),
    user_prompt: str = Form(""),
    conversation_id: Optional[int] = Form(None),
    user_id: int = Depends(get_current_user_id)
):
    try:
        file_bytes = None
        filename = None

        if file is not None:
            _validate_upload(file)
            file_bytes = await file.read()
            filename = file.filename
            if not file_bytes:
                raise HTTPException(status_code=400, detail="上传文件为空")

        source_material = _prepare_source_material(
            file_bytes=file_bytes,
            filename=filename,
            source_url=source_url,
            raw_text=raw_text,
        )

        if conversation_id is None:
            conv_id = create_conversation(user_id, title=f"{content_type} - {filename or '文本输入'}")
        else:
            conv_id = conversation_id

        # 存储用户输入
        user_input_summary = f"生成类型: {content_type}\n额外提示: {user_prompt}" if user_prompt else f"生成类型: {content_type}"
        add_message(conv_id, "user", user_input_summary)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    async def generator_with_storage():
        accumulated_result = {}
        async for chunk in stream_content_generation_agent(
            source_material=source_material,
            content_type=content_type,
            user_prompt=user_prompt,
        ):
            yield chunk
            # 可以在这里解析 chunk 收集最终结果，但更简单的方法是在流结束后从 agent 内部状态获取。
            # 由于 stream_content_generation_agent 只 yield SSE 事件，无法直接拿到最终结果。
            # 所以我们选择在生成器结束后调用同步版本获取一次结果存入数据库（代价是生成两次）。
            # 或者修改 stream_content_generation_agent 使其也能返回最终数据。
            # 这里演示一种简化方式：流结束后，调用同步版本获取结果（会重复执行 LLM）。
        # 获取最终结果存入数据库
        try:
            final_result = run_content_generation_agent(
                source_material=source_material,
                content_type=content_type,
                user_prompt=user_prompt,
            )
            assistant_content = json.dumps(final_result["final_data"], ensure_ascii=False, indent=2)
            add_message(conv_id, "assistant", assistant_content)
        except Exception:
            pass  # 存储失败不影响主流程

    return StreamingResponse(generator_with_storage(), media_type="text/event-stream")


if __name__ == "__main__":
    # 启动方法：在backend目录下执行uvicorn main:app --reload --host 0.0.0.0 --port 8000
    print("http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
