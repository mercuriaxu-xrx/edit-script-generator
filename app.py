# ==================== app.py (数据持久化版) ====================
import streamlit as st
import docx
import json
from io import BytesIO
from datetime import datetime
import os

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

# ==================== 2. 数据持久化功能 ====================
SAVE_DIR = "saved_projects"

def ensure_save_dir():
    """确保保存目录存在"""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def save_project():
    """保存当前项目到本地"""
    ensure_save_dir()
    project_name = st.session_state.get('project_name', f'项目_{datetime.now().strftime("%m%d_%H%M")}')
    filename = f"{project_name}.json"
    
    data = {
        'project_name': project_name,
        'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'selected_clips': st.session_state.get('selected_clips', []),
        'segments': st.session_state.get('segments', []),
        'field_notes_lines': st.session_state.get('field_notes_lines', []),
        'api_key': st.session_state.get('api_key', '')
    }
    
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

def load_project(filename):
    """从本地加载项目"""
    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.session_state.selected_clips = data.get('selected_clips', [])
        st.session_state.segments = data.get('segments', [])
        st.session_state.field_notes_lines = data.get('field_notes_lines', [])
        st.session_state.api_key = data.get('api_key', '')
        st.session_state.project_name = data.get('project_name', '')
        return True
    return False

def get_saved_projects():
    """获取所有已保存的项目列表"""
    ensure_save_dir()
    projects = []
    for f in os.listdir(SAVE_DIR):
        if f.endswith('.json'):
            filepath = os.path.join(SAVE_DIR, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    projects.append({
                        'filename': f,
                        'name': data.get('project_name', f),
                        'saved_at': data.get('saved_at', '未知')
                    })
            except:
                pass
    return sorted(projects, key=lambda x: x['saved_at'], reverse=True)

def delete_project(filename):
    """删除已保存的项目"""
    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

# ==================== 3. 初始化状态 ====================
if 'field_notes_lines' not in st.session_state:
    st.session_state.field_notes_lines = []
if 'selected_clips' not in st.session_state:
    st.session_state.selected_clips = []
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'project_name' not in st.session_state:
    st.session_state.project_name = f'项目_{datetime.now().strftime("%m%d_%H%M")}'
if 'auto_save' not in st.session_state:
    st.session_state.auto_save = True

# ==================== 4. 侧边栏 (增强版) ====================
with st.sidebar:
    st.title("⚙️ 设置")
    st.markdown("1. 上传场记稿 → 2. 输入内容按 Enter 标记 → 3. 分段 → 4. 保存 → 5. 导出")
    
    st.divider()
    st.markdown("**💾 项目保存**")
    
    # 项目名称
    st.session_state.project_name = st.text_input("项目名称", value=st.session_state.project_name, label_visibility="collapsed")
    
    # 保存按钮
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 保存", use_container_width=True):
            filepath = save_project()
            st.success(f"已保存！")
    with col_s2:
        if st.button("📂 加载", use_container_width=True):
            st.session_state.show_load_modal = True
    
    # 自动保存开关
    auto_save = st.checkbox("自动保存", value=st.session_state.auto_save)
    st.session_state.auto_save = auto_save
    
    if auto_save:
        st.info("✅ 每次操作后自动保存")
    
    # 已保存项目列表
    st.divider()
    st.markdown("**📁 已保存项目**")
    projects = get_saved_projects()
    if projects:
        for proj in projects[:5]:  # 只显示最近 5 个
            with st.expander(f"📄 {proj['name']}", expanded=False):
                st.write(f"保存时间：{proj['saved_at']}")
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    if st.button("加载", key=f"load_{proj['filename']}", use_container_width=True):
                        load_project(proj['filename'])
                        st.success("已加载！")
                        st.rerun()
                with col_l2:
                    if st.button("删除", key=f"del_{proj['filename']}", use_container_width=True):
                        delete_project(proj['filename'])
                        st.warning("已删除！")
                        st.rerun()
    else:
        st.info("暂无保存的项目")
    
    st.divider()
    st.markdown("**🤖 AI 设置**")
    api_key_input = st.text_input("通义千问 API Key", type="password", value=st.session_state.api_key, label_visibility="collapsed")
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    st.divider()
    st.markdown(f"📦 已标记：**{len(st.session_state.selected_clips)}** 段")
    st.markdown(f"📑 已分段：**{len(st.session_state.segments)}** 个")

# ==================== 5. 自动保存触发器 ====================
def auto_save_if_enabled():
    """如果启用自动保存，则保存项目"""
    if st.session_state.auto_save and st.session_state.selected_clips:
        save_project()

# ==================== 6. 主界面 ====================
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
            auto_save_if_enabled()  # 自动保存
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
                st.session_state.selected_clips.append({
                    "content": mark_text,
                    "timecode": mark_time,
                    "location": mark_loc,
                    "notes": ""
                })
                st.toast(f"已标记：{mark_text[:10]}...", icon="✅")
                auto_save_if_enabled()  # 自动保存
            else:
                st.toast("内容重复", icon="⚠️")

    # --- 第 4 步：素材库 ---
    if st.session_state.selected_clips:
        with st.expander(f"📦 素材库 ({len(st.session_state.selected_clips)}段)", expanded=True):
            search = st.text_input("🔍 搜索素材", placeholder="关键词...", label_visibility="collapsed")
            
            for i, clip in enumerate(st.session_state.selected_clips):
                if search and search not in clip['content']:
                    continue
                
                col_c1, col_c2, col_c3, col_c4 = st.columns([10, 2, 2, 1])
                with col_c1:
                    new_content = st.text_input(f"内容_{i}", value=clip['content'], label_visibility="collapsed", key=f"inp_{i}")
                    if new_content != clip['content']:
                        clip['content'] = new_content
                        auto_save_if_enabled()  # 自动保存
                with col_c2:
                    clip['timecode'] = st.text_input(f"时间_{i}", value=clip['timecode'], label_visibility="collapsed", key=f"time_{i}")
                with col_c3:
                    clip['location'] = st.text_input(f"地点_{i}", value=clip['location'], label_visibility="collapsed", key=f"loc_{i}")
                with col_c4:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.selected_clips.pop(i)
                        auto_save_if_enabled()  # 自动保存
                        st.rerun()

    # --- 第 5 步：分段管理 ---
    st.markdown("### 📑 分段管理")
    
    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        new_seg = st.text_input("新分段名称", placeholder="如：咖啡巴士引入", label_visibility="collapsed")
    with col_s2:
        if st.button("➕ 添加分段", use_container_width=True):
            if new_seg:
                st.session_state.segments.append({"name": new_seg, "clip_indices": [], "os_custom": ""})
                auto_save_if_enabled()  # 自动保存
                st.rerun()
    
    for i, seg in enumerate(st.session_state.segments):
        with st.expander(f"分段{i+1}: {seg['name']}", expanded=True):
            st.markdown("**分配素材 (勾选即可)**")
            cols = st.columns(3)
            for j, clip in enumerate(st.session_state.selected_clips):
                with cols[j % 3]:
                    if st.checkbox(f"`{j+1}` {clip['content'][:15]}...", value=j in seg['clip_indices'], key=f"chk_{i}_{j}"):
                        if j not in seg['clip_indices']:
                            seg['clip_indices'].append(j)
                            auto_save_if_enabled()  # 自动保存
                    else:
                        if j in seg['clip_indices']:
                            seg['clip_indices'].remove(j)
                            auto_save_if_enabled()  # 自动保存
            
            col_os1, col_os2 = st.columns([3, 1])
            with col_os1:
                seg['os_custom'] = st.text_area("OS 旁白", value=seg['os_custom'], height=50, placeholder="输入或 AI 生成...", label_visibility="collapsed", key=f"os_{i}")
            with col_os2:
                if st.button("🤖 AI 生成", key=f"ai_{i}", use_container_width=True):
                    if st.session_state.api_key:
                        try:
                            import dashscope
                            from dashscope import Generation
                            dashscope.api_key = st.session_state.api_key
                            context_list = [st.session_state.selected_clips[idx]['content'] for idx in seg['clip_indices'][:3]]
                            context = "\n".join(context_list)
                            
                            prompt = f"你是《下一站》电视节目编导，请根据以下采访内容，写一句探访人视角的 OS 旁白。要求：1. 第一人称'我'；2. 情感表达或补充说明；3. 30 字以内。内容：{context}"
                            
                            response = Generation.call(model='qwen-turbo', prompt=prompt, timeout=30)
                            
                            if response.status_code == 200:
                                seg['os_custom'] = response.output.text.strip()
                                auto_save_if_enabled()  # 自动保存
                                st.success("✅ 生成成功")
                                st.rerun()
                            else:
                                st.error(f"❌ AI 失败：{response.code}")
                        except Exception as e:
                            st.error(f"❌ 系统异常：{str(e)}")
                    else:
                        st.warning("⚠️ 请先在侧边栏配置 API Key")
            
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
                                auto_save_if_enabled()  # 自动保存
                                st.rerun()
                    with c4:
                        if st.button("⬇️", key=f"down_{i}_{idx_pos}"):
                            if idx_pos < len(seg['clip_indices']) - 1:
                                seg['clip_indices'][idx_pos], seg['clip_indices'][idx_pos+1] = seg['clip_indices'][idx_pos+1], seg['clip_indices'][idx_pos]
                                auto_save_if_enabled()  # 自动保存
                                st.rerun()

    # --- 第 6 步：导出 ---
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
