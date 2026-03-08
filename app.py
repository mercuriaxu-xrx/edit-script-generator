# ==================== app.py ====================
import streamlit as st
import docx
import re
import json
from io import BytesIO
from datetime import datetime

# 页面配置
st.set_page_config(page_title="《下一站》剪辑稿生成器", layout="wide")

# 标题
st.title("🎬 《下一站》剪辑稿智能生成系统")
st.markdown("---")

# 初始化会话状态
if 'selected_clips' not in st.session_state:
    st.session_state.selected_clips = []
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'field_notes_marked' not in st.session_state:
    st.session_state.field_notes_marked = ""

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📖 使用说明")
    st.write("1. 上传场记稿文件")
    st.write("2. 选中内容→复制→粘贴→标记")
    st.write("3. 添加分段和OS建议")
    st.write("4. 生成并下载两个文档")
    
    st.header("📋 格式规范")
    st.write("- OS旁白：`OS：内容//`")
    st.write("- 实况对话：`内容//`")
    st.write("- 空镜说明：`【空镜说明】`")
    st.write("- 剪辑点：`//` 自动添加")
    st.write("- 语序调整：`【调整语序】`")

# ==================== 主界面 ====================
# 第1部分：文件上传
st.header("📄 第1步：上传场记稿")
uploaded_file = st.file_uploader("上传场记稿(.docx)", type=["docx"])

if uploaded_file:
    # 读取文档
    doc = docx.Document(uploaded_file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    
    field_notes_text = "\n".join(full_text)
    st.session_state.field_notes_original = field_notes_text
    
    # 显示场记稿预览
    with st.expander("📋 场记稿预览"):
        st.text_area("原始内容", field_notes_text, height=300)

# 第2部分：标记高光内容
st.header("✂️ 第2步：标记高光内容")
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("添加实况内容")
    selected_text = st.text_area("复制场记稿中的内容到这里", height=100, key="selected_text")
    
    col_time1, col_time2 = st.columns(2)
    with col_time1:
        timecode = st.text_input("时间码（可选）", placeholder="如：3:59")
    with col_time2:
        speaker = st.text_input("讲话人（可选）", placeholder="如：讲话人1")
    
    location = st.text_input("地点/场景（用于分段）", placeholder="如：咖啡巴士/红枫林/马术基地")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ 标记选中内容", use_container_width=True):
            if selected_text:
                clip = {
                    "content": selected_text.strip(),
                    "timecode": timecode,
                    "speaker": speaker,
                    "location": location,
                    "type": "实况",
                    "notes": ""
                }
                st.session_state.selected_clips.append(clip)
                st.success(f"已添加！当前共 {len(st.session_state.selected_clips)} 段素材")
    
    with col_btn2:
        if st.button("🗑️ 清空所有", use_container_width=True):
            st.session_state.selected_clips = []
            st.success("已清空")

with col2:
    st.subheader("📦 已标记素材库")
    if st.session_state.selected_clips:
        for i, clip in enumerate(st.session_state.selected_clips):
            with st.expander(f"素材{i+1} [{clip['location'] or '未分段'}] {clip['timecode'] or ''}"):
                st.write(f"**内容:** {clip['content']}")
                st.write(f"**讲话人:** {clip['speaker'] or '-'}")
                
                # 编辑内容
                new_content = st.text_area("编辑内容", clip['content'], height=80, key=f"edit_{i}")
                if new_content != clip['content']:
                    clip['content'] = new_content
                
                # 添加备注
                notes = st.text_input("备注（如：调整语序）", clip['notes'], key=f"notes_{i}")
                clip['notes'] = notes
                
                # 删除按钮
                if st.button(f"删除", key=f"del_{i}"):
                    st.session_state.selected_clips.pop(i)
                    st.rerun()
    else:
        st.info("暂无标记素材，请在左侧添加")

# 第3部分：分段管理
st.header("📑 第3步：分段管理")
st.write("根据**地点**和**内容主题**变化进行分段")

if st.session_state.selected_clips:
    # 自动提取地点
    locations = list(set([clip['location'] for clip in st.session_state.selected_clips if clip['location']]))
    
    if locations:
        st.write(f"📍 检测到的地点/场景：{', '.join(locations)}")
    
    # 手动添加分段
    col_seg1, col_seg2 = st.columns([2, 1])
    with col_seg1:
        new_segment_name = st.text_input("新分段名称（地点/主题）", placeholder="如：咖啡巴士引入/红枫林观景")
    with col_seg2:
        if st.button("➕ 添加分段"):
            if new_segment_name:
                st.session_state.segments.append({
                    "name": new_segment_name,
                    "clips": [],
                    "os_suggestion": ""
                })
                st.success(f"已添加分段：{new_segment_name}")
    
    # 显示分段
    if st.session_state.segments:
        st.subheader("当前分段")
        for i, seg in enumerate(st.session_state.segments):
            with st.expander(f"分段{i+1}: {seg['name']}", expanded=True):
                # 分配素材到分段
                st.write("分配素材到此分段：")
                available_clips = [c for c in st.session_state.selected_clips if c['location'] == seg['name'] or not c['location']]
                for j, clip in enumerate(st.session_state.selected_clips):
                    if st.checkbox(f"素材{j+1}: {clip['content'][:50]}...", key=f"seg_{i}_clip_{j}"):
                        if j not in seg['clips']:
                            seg['clips'].append(j)
                
                # OS建议
                os_suggestion = st.text_area("OS建议（探访人视角）", seg['os_suggestion'], 
                                           height=60, 
                                           placeholder="如：边喝咖啡，边欣赏沿路美景...",
                                           key=f"os_{i}")
                seg['os_suggestion'] = os_suggestion
                
                # 删除分段
                if st.button(f"删除此分段", key=f"del_seg_{i}"):
                    st.session_state.segments.pop(i)
                    st.rerun()
    else:
        st.info("请先添加分段，然后将素材分配到各分段")

# 第4部分：AI生成OS建议
st.header("🤖 第4步：AI生成OS建议（可选）")
st.write("根据上下文自动生成探访人视角的旁白建议")

use_ai = st.checkbox("启用AI生成OS建议（需要API Key）")

if use_ai:
    api_key = st.text_input("OpenAI API Key", type="password")
    
    if st.button("生成OS建议"):
        if api_key and st.session_state.segments:
            st.info("正在生成OS建议...（模拟）")
            # 这里可以接入真实的AI API
            # 目前提供模板建议
            os_templates = [
                "带着期待，我踏上了下一段旅程。",
                "眼前的景象，比我想象中更加震撼。",
                "这一刻，我仿佛理解了他们坚守的意义。",
                "山水与人文，在这里完美融合。",
                "每一次对话，都让我对这座城市有了更深的了解。"
            ]
            for i, seg in enumerate(st.session_state.segments):
                if not seg['os_suggestion']:
                    seg['os_suggestion'] = os_templates[i % len(os_templates)]
            st.success("OS建议已生成！")
        else:
            st.warning("请输入API Key或先添加分段")

# 第5部分：预览和导出
st.header("💾 第5步：预览和导出")

if st.button("📝 生成剪辑稿预览"):
    # 生成剪辑稿内容
    edit_script = ""
    
    for seg_idx, seg in enumerate(st.session_state.segments):
        # 添加分段标题
        edit_script += f"【分段{seg_idx+1}: {seg['name']}】\n\n"
        
        # 添加OS
        if seg['os_suggestion']:
            edit_script += f"OS：{seg['os_suggestion']}//\n\n"
        
        # 添加实况内容
        for clip_idx in seg['clips']:
            if clip_idx < len(st.session_state.selected_clips):
                clip = st.session_state.selected_clips[clip_idx]
                
                # 添加备注
                if clip['notes']:
                    edit_script += f"【{clip['notes']}】\n"
                
                # 添加时间码和讲话人
                timecode_str = f"{clip['timecode']} " if clip['timecode'] else ""
                speaker_str = f"{clip['speaker']} " if clip['speaker'] else ""
                
                # 添加内容（自动添加//）
                edit_script += f"{timecode_str}{speaker_str}{clip['content']}//\n\n"
        
        edit_script += "\n" + "="*50 + "\n\n"
    
    # 如果没有分段，使用所有素材
    if not st.session_state.segments and st.session_state.selected_clips:
        for clip in st.session_state.selected_clips:
            timecode_str = f"{clip['timecode']} " if clip['timecode'] else ""
            speaker_str = f"{clip['speaker']} " if clip['speaker'] else ""
            edit_script += f"{timecode_str}{speaker_str}{clip['content']}//\n\n"
    
    st.session_state.edit_script_preview = edit_script
    
    # 显示预览
    st.subheader("剪辑稿预览")
    st.text_area("预览内容", edit_script, height=400)

# 导出按钮
col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("📥 下载剪辑稿(.docx)", use_container_width=True):
        if 'edit_script_preview' in st.session_state:
            # 创建Word文档
            doc = docx.Document()
            doc.add_heading('《下一站》剪辑稿', 0)
            doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            doc.add_paragraph(st.session_state.edit_script_preview)
            
            # 保存到内存
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            # 提供下载
            st.download_button(
                label="点击下载剪辑稿",
                data=buffer,
                file_name=f"剪辑稿_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("请先生成预览")

with col_export2:
    if st.button("📥 下载标记场记稿(.docx)", use_container_width=True):
        if uploaded_file:
            # 创建标记后的场记稿
            doc = docx.Document()
            doc.add_heading('《下一站》场记稿（已标记）', 0)
            doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            doc.add_paragraph(f"已标记素材数量：{len(st.session_state.selected_clips)}\n")
            
            # 添加原始内容
            doc.add_heading('原始场记稿', level=1)
            doc.add_paragraph(field_notes_text)
            
            # 添加标记内容列表
            doc.add_heading('已标记高光内容', level=1)
            for i, clip in enumerate(st.session_state.selected_clips):
                p = doc.add_paragraph()
                p.add_run(f"【标记{i+1}】").bold = True
                p.add_run(f" 时间码：{clip['timecode'] or '-'}  ")
                p.add_run(f"地点：{clip['location'] or '-'}\n")
                p.add_run(clip['content'])
            
            # 保存到内存
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            # 提供下载
            st.download_button(
                label="点击下载标记场记稿",
                data=buffer,
                file_name=f"场记稿_已标记_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("请先上传场记稿")

# 页脚
st.markdown("---")
st.caption("《下一站》节目组内部工具 | 版本 2.0 | 满足5大核心需求")
# ==================== 代码结束 ====================
