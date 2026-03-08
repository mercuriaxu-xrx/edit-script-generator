# ==================== app.py (预览修复版) ====================
import streamlit as st
import docx
from io import BytesIO
from datetime import datetime

# 页面配置
st.set_page_config(page_title="《下一站》剪辑稿生成器", layout="wide", page_icon="🎬")

# ==================== 1. 界面瘦身 (CSS 优化) ====================
st.markdown("""
<style>
    /* 缩小标题字体 */
    h1 {font-size: 1.4rem !important; margin-bottom: 0.5rem !important;}
    h2 {font-size: 1.1rem !important; margin-bottom: 0.5rem !important;}
    h3 {font-size: 1.0rem !important; margin-bottom: 0.3rem !important;}
    /* 缩小正文字体 */
    .stMarkdown, p, label, div[data-testid="stWidgetLabel"] {font-size: 0.85rem !important;}
    /* 缩小输入框和按钮 */
    .stTextInput input, .stTextArea textarea {font-size: 0.85rem !important; padding: 5px !important;}
    .stButton button {font-size: 0.85rem !important; padding: 5px 10px !important;}
    /* 减少间距 */
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .stExpander {margin-bottom: 0.5rem !important;}
    /* 隐藏底部菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 2. 性能优化 (缓存加载) ====================
@st.cache_data
def load_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return ""

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
if 'show_preview' not in st.session_state:
    st.session_state.show_preview = False

# ==================== 4. 侧边栏 (紧凑版) ====================
with st.sidebar:
    st.title("⚙️ 设置")
    st.markdown("1. 上传场记稿 → 2. 勾选显示预览 → 3. 复制内容按 Enter 标记 → 4. 分段 → 5. 导出")
    
    st.divider()
    st.markdown("**AI 设置**")
    api_key_input = st.text_input("通义千问 API Key", type="password", value=st.session_state.api_key, label_visibility="collapsed")
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    if st.session_state.api_key:
        if st.button("🔑 测试 Key", use_container_width=True, type="primary"):
            try:
                import dashscope
                from dashscope import Generation
                dashscope.api_key = st.session_state.api_key
                resp = Generation.call(model='qwen-turbo', prompt='test')
                if resp.status_code == 200:
                    st.session_state.ai_enabled = True
                    st.success("AI 可用")
                else:
                    st.error("Key 无效")
            except:
                st.error("连接失败")
    
    if st.session_state.ai_enabled:
        st.success("🤖 AI 功能已启用")
    else:
        st.warning("⚠️ AI 功能未启用，将使用模板生成")
    
    st.divider()
    st.markdown(f"已标记：**{len(st.session_state.selected_clips)}** 段")
    st.markdown(f"已分段：**{len(st.session_state.segments)}** 个")

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
        text = load_docx(uploaded_file)
        st.session_state.field_notes_lines = text.split('\n')
        st.session_state.last_file = uploaded_file.name
        st.session_state.show_preview = True  # 上传后默认显示预览

    # --- 新增：预览控制按钮 ---
    st.markdown("### 👁️ 场记稿预览区")
    show_preview = st.checkbox("显示场记稿原文 (方便复制)", value=st.session_state.show_preview, key="preview_toggle")
    st.session_state.show_preview = show_preview

    if show_preview:
        full_text = "\n".join(st.session_state.field_notes_lines)
        st.text_area("原始内容 (可直接复制)", full_text, height=250, label_visibility="collapsed")
        st.info("💡 操作提示：点击上方文本框中的内容 → 复制 → 粘贴到下方标记
