import os
import sys
import time
from pathlib import Path
import streamlit as st
import requests

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Streamlit Page Config
st.set_page_config(
    page_title="Multi-Tool AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #6B7280;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .trace-box {
        background-color: #F8FAFC;
        border-left: 4px solid #4F46E5;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85rem;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# Sidebar: Controls & Live Task Manager
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/bot.png", width=64)
    st.title("Control Panel")
    
    # API Backend Connection Status Check
    backend_online = False
    try:
        r = requests.get(f"{st.session_state.api_url}/health", timeout=1.5)
        if r.status_code == 200:
            backend_online = True
    except Exception:
        backend_online = False

    if backend_online:
        st.success("🟢 FastAPI Backend: Connected")
    else:
        st.warning("🟡 Direct Agent Mode (FastAPI offline, running locally)")

    st.divider()

    # Agent Model Settings
    st.subheader("⚙️ Agent Settings")
    provider = st.selectbox(
        "LLM Provider",
        options=["Groq", "OpenAI", "Google", "Mock / Offline"],
        index=0 if os.getenv("GROQ_API_KEY") else 3,
        help="Select which AI engine to use. 'Mock / Offline' requires no API key!"
    )
    
    api_key = None
    if provider == "Groq":
        default_model = "llama-3.3-70b-versatile"
        api_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    elif provider == "OpenAI":
        default_model = "gpt-4o-mini"
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    elif provider == "Google":
        default_model = "gemini-1.5-flash"
        api_key = st.text_input("Google API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""))
    else:
        default_model = "mock-agent-v1"
        st.caption("Running with built-in deterministic agent. All tools work without external API keys.")

    model_name = st.text_input("Model ID", value=default_model)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

    st.divider()

    # Conversation Actions
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.rerun()

    st.caption(f"Active Session: `{st.session_state.session_id}`")

# Main Content Layout: Two Tabs (Chat Assistant & Task Manager)
tab_chat, tab_tasks, tab_audit = st.tabs(["💬 AI Assistant", "📋 Task Manager", "🔍 Tool Audit Logs"])

# ==========================================
# TAB 1: AI CHAT ASSISTANT
# ==========================================
with tab_chat:
    st.markdown('<div class="main-title">Multi-Tool AI Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Intelligent Task Assistant with Calculator, Web Search, and SQLite Task Management</div>', unsafe_allow_html=True)

    # Quick Example Prompts
    st.markdown("**Quick Prompts:**")
    col1, col2, col3, col4 = st.columns(4)
    quick_prompt = None
    if col1.button("🔢 25% of 800", use_container_width=True):
        quick_prompt = "What is 25% of 800?"
    if col2.button("✖️ 120 × 45", use_container_width=True):
        quick_prompt = "Calculate 120 * 45"
    if col3.button("📝 Add LangGraph Task", use_container_width=True):
        quick_prompt = "Add a task to learn LangGraph tomorrow"
    if col4.button("🔍 Search RAG", use_container_width=True):
        quick_prompt = "Find information about Retrieval-Augmented Generation"

    # Display Chat History
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])
            # Display Tool Execution Trace if present
            if msg.get("tool_calls"):
                with st.expander(f"🔧 Tool Execution Trace ({len(msg['tool_calls'])} tool call(s))", expanded=False):
                    for idx, tc in enumerate(msg["tool_calls"], 1):
                        st.markdown(f"**Step {idx}: `{tc['tool_name']}`** ({tc.get('execution_time_ms', 0)} ms)")
                        st.json({"Input": tc["tool_input"], "Output": tc["tool_output"]})

    # Chat Input handler
    user_input = st.chat_input("Ask a question, perform a calculation, or manage tasks...")
    if quick_prompt:
        user_input = quick_prompt

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Call Agent
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("AI Agent is thinking and evaluating tools..."):
                provider_code = provider.lower().split()[0]
                
                # Check if backend API is reachable
                if backend_online:
                    try:
                        payload = {
                            "message": user_input,
                            "session_id": st.session_state.session_id,
                            "provider": provider_code,
                            "model": model_name,
                            "temperature": temperature
                        }
                        resp = requests.post(f"{st.session_state.api_url}/api/chat", json=payload, timeout=60)
                        if resp.status_code == 200:
                            data = resp.json()
                            reply = data["response"]
                            tool_calls = data.get("tool_calls", [])
                        else:
                            reply = f"API Error ({resp.status_code}): {resp.text}"
                            tool_calls = []
                    except Exception as e:
                        reply = f"Failed to connect to backend: {e}"
                        tool_calls = []
                else:
                    # Run direct in-process LangGraph agent
                    from app.agent.workflow import build_agent_graph
                    from langchain_core.messages import HumanMessage
                    
                    agent_graph = build_agent_graph(
                        provider=provider_code,
                        model=model_name,
                        temperature=temperature,
                        api_key=api_key
                    )
                    inputs = {
                        "messages": [HumanMessage(content=user_input)],
                        "session_id": st.session_state.session_id,
                        "tool_calls_trace": [],
                        "iteration_count": 0,
                        "error": None
                    }
                    config = {"configurable": {"thread_id": st.session_state.session_id}}
                    result = agent_graph.invoke(inputs, config=config)
                    last_msg = result["messages"][-1]
                    reply = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
                    tool_calls = result.get("tool_calls_trace", [])

                st.markdown(reply)
                
                if tool_calls:
                    with st.expander(f"🔧 Tool Execution Trace ({len(tool_calls)} tool call(s))", expanded=True):
                        for idx, tc in enumerate(tool_calls, 1):
                            st.markdown(f"**Step {idx}: `{tc['tool_name']}`** ({tc.get('execution_time_ms', 0)} ms)")
                            st.json({"Input": tc["tool_input"], "Output": tc["tool_output"]})

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "tool_calls": tool_calls
                })

# ==========================================
# TAB 2: TASK MANAGER DASHBOARD
# ==========================================
with tab_tasks:
    st.subheader("📋 SQLite Task Manager")
    st.caption("Tasks saved and retrieved by the AI Agent or via direct control.")

    from app.db.database import SessionLocal
    from app.db import crud

    # Task Creation Form
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("new_task_form", clear_on_submit=True):
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                new_title = st.text_input("Task Title", placeholder="e.g. Learn LangGraph")
                new_desc = st.text_area("Description (optional)", placeholder="Notes or instructions...")
            with col_t2:
                new_priority = st.selectbox("Priority", options=["Low", "Medium", "High"], index=1)
                new_due = st.text_input("Due Date", placeholder="e.g. Tomorrow, 2026-11-25")
            
            submitted = st.form_submit_button("Save Task", use_container_width=True)
            if submitted and new_title.strip():
                db = SessionLocal()
                try:
                    crud.create_task(db, title=new_title, description=new_desc, priority=new_priority, due_date=new_due)
                    st.success(f"Task '{new_title}' added successfully!")
                    st.rerun()
                finally:
                    db.close()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_status = st.selectbox("Filter Status", ["All", "Pending", "Completed"], index=0)
    with col_f2:
        filter_priority = st.selectbox("Filter Priority", ["All", "Low", "Medium", "High"], index=0)

    # Retrieve Tasks
    db = SessionLocal()
    try:
        status_arg = None if filter_status == "All" else filter_status
        priority_arg = None if filter_priority == "All" else filter_priority
        tasks = crud.get_tasks(db, status=status_arg, priority=priority_arg)
        
        if not tasks:
            st.info("No tasks found. Use the chat agent ('Add a task to...') or the form above to create one!")
        else:
            for task in tasks:
                badge_class = f"badge-{task.priority.lower()}"
                col_info, col_complete, col_delete = st.columns([5, 1.2, 1])
                
                with col_info:
                    status_icon = "✅" if task.status.lower() == "completed" else "⏳"
                    st.markdown(
                        f"**#{task.id} {status_icon} {task.title}** "
                        f"<span class='{badge_class}'>{task.priority}</span>",
                        unsafe_allow_html=True
                    )
                    extra = []
                    if task.due_date:
                        extra.append(f"Due: {task.due_date}")
                    if task.description:
                        extra.append(f"Note: {task.description}")
                    if extra:
                        st.caption(" • ".join(extra))
                
                with col_complete:
                    if task.status.lower() != "completed":
                        if st.button("Complete", key=f"comp_{task.id}"):
                            crud.complete_task(db, task.id)
                            st.rerun()
                    else:
                        st.write("✓ Done")

                with col_delete:
                    if st.button("Delete", key=f"del_{task.id}"):
                        crud.delete_task(db, task.id)
                        st.rerun()
                
                st.divider()
    finally:
        db.close()

# ==========================================
# TAB 3: TOOL AUDIT LOGS
# ==========================================
with tab_audit:
    st.subheader("🔍 Tool Execution Audit Log")
    st.caption("History of tools executed by the AI Agent with inputs, outputs, and execution latencies.")
    
    db = SessionLocal()
    try:
        logs = crud.get_recent_audit_logs(db, limit=30)
        if not logs:
            st.info("No tool executions logged yet. Try asking the agent to calculate or manage tasks!")
        else:
            table_data = []
            for l in logs:
                table_data.append({
                    "ID": l.id,
                    "Tool": l.tool_name,
                    "Status": l.status,
                    "Latency (ms)": l.execution_time_ms,
                    "Input": str(l.tool_input)[:80],
                    "Output": str(l.tool_output)[:120],
                    "Time": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A"
                })
            st.dataframe(table_data, use_container_width=True)
    finally:
        db.close()
