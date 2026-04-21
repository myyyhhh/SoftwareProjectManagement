# auth.py
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

# ------------------------------
# 数据库初始化
# ------------------------------
DB_PATH = "app.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

init_db()

# ------------------------------
# 密码工具（带盐哈希）
# ------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${h.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    salt, h_hex = hashed.split('$')
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return h.hex() == h_hex

# ------------------------------
# 会话管理
# ------------------------------
SESSION_EXPIRY_DAYS = 7

def create_session(user_id: int, conn: sqlite3.Connection) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)
    conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    conn.commit()
    return token

def validate_token(token: str, conn: sqlite3.Connection) -> Optional[int]:
    """验证 token，返回 user_id，若无效返回 None"""
    cur = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token = ?",
        (token,)
    )
    row = cur.fetchone()
    if not row:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        # 过期则删除
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return None
    return row["user_id"]

def delete_session(token: str, conn: sqlite3.Connection):
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()

# ------------------------------
# Pydantic 模型
# ------------------------------
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user_id: int
    username: str

class ConversationInfo(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]]  # 包含 role 和 content

class ConversationsResponse(BaseModel):
    user_id: int
    conversations: List[ConversationInfo]

# ------------------------------
# 依赖项：从请求头获取 token 并返回 user_id
# ------------------------------
async def get_current_user_id(
    authorization: str = Header(None, alias="Authorization")
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供有效 Token")
    token = authorization[7:].strip()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        user_id = validate_token(token, conn)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token 无效或已过期")
        return user_id

# ------------------------------
# 路由定义
# ------------------------------
router = APIRouter(prefix="/auth", tags=["认证与对话历史"])

@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        # 检查用户名是否已存在
        cur = conn.execute("SELECT id FROM users WHERE username = ?", (data.username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")
        # 创建用户
        password_hash = hash_password(data.password)
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (data.username, password_hash)
        )
        user_id = cur.lastrowid
        conn.commit()
        # 自动创建会话
        token = create_session(user_id, conn)
        return {"token": token, "user_id": user_id, "username": data.username}

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (data.username,)
        )
        row = cur.fetchone()
        if not row or not verify_password(data.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        user_id = row["id"]
        token = create_session(user_id, conn)
        return {"token": token, "user_id": user_id, "username": data.username}

@router.post("/logout")
async def logout(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="无效的 Authorization 头")
    token = authorization[7:].strip()
    with sqlite3.connect(DB_PATH) as conn:
        delete_session(token, conn)
    return {"status": "已登出"}

@router.get("/conversations/{user_id}", response_model=ConversationsResponse)
async def get_conversations(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    """获取指定用户的全部对话历史（需验证 token 且 token 对应的用户与请求 user_id 一致）"""
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问其他用户的对话历史")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        # 获取所有会话
        cur = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        conversations = []
        for conv_row in cur.fetchall():
            # 获取该会话的所有消息
            msg_cur = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conv_row["id"],)
            )
            messages = [dict(msg) for msg in msg_cur.fetchall()]
            conversations.append({
                "id": conv_row["id"],
                "title": conv_row["title"],
                "created_at": conv_row["created_at"],
                "updated_at": conv_row["updated_at"],
                "messages": messages
            })
        return {"user_id": user_id, "conversations": conversations}

# ------------------------------
# 辅助函数：用于 main.py 中存储对话记录
# ------------------------------
def create_conversation(user_id: int, title: Optional[str] = None) -> int:
    """创建新会话，返回 conversation_id"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
            (user_id, title)
        )
        conn.commit()
        return cur.lastrowid

def add_message(conversation_id: int, role: str, content: str):
    """添加一条消息"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        # 更新会话的 updated_at
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()