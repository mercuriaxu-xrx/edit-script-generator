# ==================== app.py (AI功能完善版) ====================
import streamlit as st
import docx
from io import BytesIO
from datetime import datetime

# 页面配置
st.set_page_config(page_title="《下一站》剪辑稿生成器", layout="wide", page_icon="🎬")

# ==================== 1. 界面瘦身 (CSS 优化) ====================
st.markdown("""
<style>
    h1 {font-size: 1.4rem !important; margin-bottom: 0.5rem !important;}
    h2 {font-size: 1.1rem !important; margin-bottom: 0.5rem !important;}
    h3 {font-size: 1.0rem !important; margin-bottom: 0.3rem !important;}
    .stMarkdown, p, label, div[data-testid="stWidgetLabel"] {font-size: 0.85rem !important;}
    .stTextInput input, .stTextArea textarea {font-size: 0.85rem !important; padding: 5px !important;}
    .stButton button {font-size: 0.85rem !important; padding: 5px 10px !important;}
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .stExpander {margin-bottom: 0.5rem !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 2. AI 模块导入检查 ====================
ai_available = False
ai_error_msg = ""

try:
    import dashscope
    from dashscope import Generation
    ai_available = True
except ImportError as e:
    ai_error_msg = f"缺少 dashscope 库：{str(e)}"
except Exception as e:
    ai_error_msg = f"导入错误：{str(e)}"

# ==================== 3. 初始化状态 ====================
if 'field_notes_lines' not in st.session_state:
    st.session_state.field_notes_lines = []
if 'selected_clips' not in st.session_state:
    st.session_state.selected_clips = []
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'ai_enabled' not in st.session_state:
    st.session_state.ai_enabled = False

# ==================== 4. 侧边栏 (设置) ====================
with st.sidebar:
    st.title("⚙️ 设置")
    st.markdown("1. 上传场记稿 → 2. 输入内容按 Enter 标记 → 3. 分段 → 4. 导出")
    
    st.divider()
    st.markdown("**🤖 AI 设置**")
    
    # 显示库状态
    if not ai_available:
        st.error(f"❌ dashscope 未安装\n{ai_error_msg}")
        st.info("💡 请运行：`pip install dashscope`")
    else:
        st.success("✅ dashscope 库已就绪")
    
    api_key_input = st.text_input(
        "通义千问 API Key", 
        type="password", 
        value=st.session_state.api_key, 
        label_visibility="collapsed",
        help="获取地址：https://dashscope.console.aliyun.com/"
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    # AI 测试按钮
    if st.session_state.api_key and ai_available:
        if st.button("🔑 测试 AI 连接", use_container_width=True, type="primary"):
            with st.spinner("正在测试..."):
                try:
                    dashscope.api_key = st.session_state.api_key
                    response = Generation.call(
                        model='qwen-turbo',
                        prompt='请用一句话介绍你自己',
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        st.session_state.ai_enabled = True
                        st.success("✅ AI 连接成功！")
                    else:
                        st.session_state.ai_enabled = False
                        st.error(f"❌ API 错误：{response.code}\n{response.message if hasattr(response, 'message') else '未知错误'}")
                        
                except Exception as e:
                    st.session_state.ai_enabled = False
                    st.error(f"❌ 连接异常：{type(e).__name__}\n{str(e)}")
    
    # 显示 AI 状态
    st.divider()
    if st.session_state.ai_enabled:
        st.success("🤖 AI 功能：**已启用**")
    elif st.session_state.api_key:
        st.warning("⚠️ AI 功能：**Key 已输入但未验证**")
    else:
        st.warning("⚠️ AI 功能：**未配置**")
    
    st.divider()
    st.markdown(f"📦 已标记：**{len(st.session_state.selected_clips)}** 段")
    st.markdown(f"📑 已分段：**{len(st.session_state.segments)}** 个")

# ==================== 5. 主界面 ====================
st.title("🎬 《下一站》剪辑稿生成系统")

# --- 第 1 步：上传 ---
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("上传场记稿 (.docx)", type=["docx"], label_visibility="collapsed")
with col_up2:
    if uploaded_file:
        st.success("上传成功")

if uploaded_file:
    # 仅当文件变化时重新加载
    if 'last_file' not in st.session_state or st.session_state.last_file != uploaded_file.name:
        try:
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            st.session_state.field_notes_lines = text.split('\n')
            st.session_state.last_file = uploaded_file.name
            st.session_state.show_preview = True
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}")

    # --- 第 2 步：预览 ---
    st.markdown("### 👁️ 场记稿预览区")
    show_preview = st.checkbox("显示场记稿原文 (方便复制)", value=st.session_state.get('show_preview', False), key="preview_toggle")
    st.session_state.show_preview = show_preview

    if show_preview:
        full_text = "\n".join(st.session_state.field_notes_lines)
        st.text_area("原始内容 (可直接复制)", full_text, height=250, label_visibility="collapsed")
        st.info("💡 操作提示：点击上方文本框中的内容 → 复制 → 粘贴到下方标记框 → 按 Enter 键")
    
    st.divider()

    # --- 第 3 步：标记 ---
    st.markdown("### ✏️ 标记内容 (输入后按 Enter 自动标记)")
    
    with st.form("mark_form", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns([4, 1, 1])
        with col_m1:
            mark_text = st.text_input("粘贴一小句内容", placeholder="例如：你要喝点什么吗？", label_visibility="collapsed")
        with col_m2:
            mark_time = st.text_input("时间码", placeholder="3:59", label_visibility="collapsed")
        with col_m3:
            mark_loc = st.text_input("地点", placeholder="咖啡巴士", label_visibility="collapsed")
        
        submitted = st.form_submit_button("✅ 标记", use_container_width=True, type="primary")
        
        if submitted and mark_text:
            if not any(c['content'] == mark_text for c in st.session_state.selected_clips):
               
