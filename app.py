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
        st.info("💡 操作提示：点击上方文本框中的内容 → 复制 → 粘贴到下方标记框 → 按 Enter 键")
    
    st.divider()

    # --- 第 2 步：标记 (支持 Enter 键) ---
    st.markdown("### ✏️ 标记内容 (输入后按 Enter 自动标记)")
    
    # 使用 form 实现 Enter 提交
    with st.form("mark_form", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns([4, 1, 1])
        with col_m1:
            # text_input 支持按 Enter 提交表单
            mark_text = st.text_input("粘贴一小句内容", placeholder="例如：你要喝点什么吗？", label_visibility="collapsed")
        with col_m2:
            mark_time = st.text_input("时间码", placeholder="3:59", label_visibility="collapsed")
        with col_m3:
            mark_loc = st.text_input("地点", placeholder="咖啡巴士", label_visibility="collapsed")
        
        # 表单提交按钮 (点击或按 Enter 均可)
        submitted = st.form_submit_button("✅ 标记", use_container_width=True, type="primary")
        
        if submitted and mark_text:
            # 查重
            if not any(c['content'] == mark_text for c in st.session_state.selected_clips):
                st.session_state.selected_clips.append({
                    "content": mark_text,
                    "timecode": mark_time,
                    "location": mark_loc,
                    "notes": ""
                })
                st.toast(f"已标记：{mark_text[:10]}...", icon="✅")
            else:
                st.toast("内容重复", icon="⚠️")

    # --- 第 3 步：素材库 (优化显示) ---
    if st.session_state.selected_clips:
        with st.expander(f"📦 素材库 ({len(st.session_state.selected_clips)}段)", expanded=True):
            # 搜索
            search = st.text_input("🔍 搜索素材", placeholder="关键词...", label_visibility="collapsed")
            
            # 列表显示 (简化版)
            for i, clip in enumerate(st.session_state.selected_clips):
                if search and search not in clip['content']:
                    continue
                
                col_c1, col_c2, col_c3, col_c4 = st.columns([10, 2, 2, 1])
                with col_c1:
                    # 直接编辑内容
                    new_content = st.text_input(f"内容_{i}", value=clip['content'], label_visibility="collapsed", key=f"inp_{i}")
                    if new_content != clip['content']:
                        clip['content'] = new_content
                with col_c2:
                    clip['timecode'] = st.text_input(f"时间_{i}", value=clip['timecode'], label_visibility="collapsed", key=f"time_{i}")
                with col_c3:
                    clip['location'] = st.text_input(f"地点_{i}", value=clip['location'], label_visibility="collapsed", key=f"loc_{i}")
                with col_c4:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.selected_clips.pop(i)
                        st.rerun()

    # --- 第 4 步：分段管理 ---
    st.markdown("### 📑 分段管理")
    
    # 添加分段
    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        new_seg = st.text_input("新分段名称", placeholder="如：咖啡巴士引入", label_visibility="collapsed")
    with col_s2:
        if st.button("➕ 添加分段", use_container_width=True):
            if new_seg:
                st.session_state.segments.append({"name": new_seg, "clip_indices": [], "os_custom": ""})
                st.rerun()
    
    # 显示分段
    for i, seg in enumerate(st.session_state.segments):
        with st.expander(f"分段{i+1}: {seg['name']}", expanded=True):
            # 分配素材
            st.markdown("**分配素材 (勾选即可)**")
            cols = st.columns(3)
            for j, clip in enumerate(st.session_state.selected_clips):
                with cols[j % 3]:
                    if st.checkbox(f"`{j+1}` {clip['content'][:15]}...", value=j in seg['clip_indices'], key=f"chk_{i}_{j}"):
                        if j not in seg['clip_indices']:
                            seg['clip_indices'].append(j)
                    else:
                        if j in seg['clip_indices']:
                            seg['clip_indices'].remove(j)
            
            # 调整顺序 & OS
            col_os1, col_os2 = st.columns([3, 1])
            with col_os1:
                seg['os_custom'] = st.text_area("OS 旁白", value=seg['os_custom'], height=50, placeholder="输入或 AI 生成...", label_visibility="collapsed", key=f"os_{i}")
            with col_os2:
                if st.button("🤖 AI 生成", key=f"ai_{i}", use_container_width=True):
                    if st.session_state.ai_enabled:
                        try:
                            import dashscope
                            from dashscope import Generation
                            dashscope.api_key = st.session_state.api_key
                            context = "\n".join([st.session_state.selected_clips[idx]['content'] for idx in seg['clip_indices'][:3]])
                            resp = Generation.call(model='qwen-turbo', prompt=f"写一句探访人视角的 OS，30 字内，内容：{context}")
                            if resp.status_code == 200:
                                seg['os_custom'] = resp.output.text.strip()
                                st.rerun()
                        except:
                            st.error("AI 失败")
                    else:
                        st.warning("请先配置 Key")
            
            # 已选素材排序
            if seg['clip_indices']:
                st.markdown("**已选顺序 (上移/下移)**")
                for idx_pos, clip_idx in enumerate(seg['clip_indices']):
                    clip = st.session_state.selected_clips[clip_idx]
                    c1, c2, c3, c4 = st.columns([1, 8, 1, 1])
                    with c1:
                        st.write(f"{idx_pos+1}")
                    with c2:
                        st.write(clip['content'][:40])
                    with c3:
                        if st.button("⬆️", key=f"up_{i}_{idx_pos}"):
                            if idx_pos > 0:
                                seg['clip_indices'][idx_pos], seg['clip_indices'][idx_pos-1] = seg['clip_indices'][idx_pos-1], seg['clip_indices'][idx_pos]
                                st.rerun()
                    with c4:
                        if st.button("⬇️", key=f"down_{i}_{idx_pos}"):
                            if idx_pos < len(seg['clip_indices']) - 1:
                                seg['clip_indices'][idx_pos], seg['clip_indices'][idx_pos+1] = seg['clip_indices'][idx_pos+1], seg['clip_indices'][idx_pos]
                                st.rerun()

    # --- 第 5 步：导出 ---
    st.markdown("### 💾 导出")
    if st.button("📝 生成预览", type="primary"):
        script = ""
        for i, seg in enumerate(st.session_state.segments):
            script += f"【分段{i+1}: {seg['name']}】\n"
            if seg['os_custom']:
                script += f"OS：{seg['os_custom']}//\n"
            content = " ".join([f"{st.session_state.selected_clips[idx]['content']}//" for idx in seg['clip_indices']])
            script += f"{content}\n\n" + "="*30 + "\n\n"
        st.session_state.edit_script_preview = script
        st.text_area("预览", script, height=200)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if st.button("📥 下载剪辑稿", use_container_width=True):
            if 'edit_script_preview' in st.session_state:
                doc = docx.Document()
                doc.add_heading('剪辑稿', 0)
                doc.add_paragraph(st.session_state.edit_script_preview)
                buf = BytesIO()
                doc.save(buf)
                st.download_button("点击下载", buf, f"剪辑稿_{datetime.now().strftime('%m%d')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    with col_e2:
        if st.button("📥 下载标记稿", use_container_width=True):
            doc = docx.Document()
            doc.add_heading('标记场记稿', 0)
            for line in st.session_state.field_notes_lines:
                marked = False
                for clip in st.session_state.selected_clips:
                    if clip['content'] in line:
                        p = doc.add_paragraph()
                        parts = line.split(clip['content'])
                        for k, part in enumerate(parts):
                            if part: p.add_run(part)
                            if k < len(parts)-1:
                                r = p.add_run(clip['content'])
                                r.font.highlight_color = docx.enum.text.WD_COLOR_INDEX.YELLOW
                        marked = True
                        break
                if not marked:
                    doc.add_paragraph(line)
            buf = BytesIO()
            doc.save(buf)
            st.download_button("点击下载", buf, f"场记稿_{datetime.now().strftime('%m%d')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ==================== 代码结束 ====================
