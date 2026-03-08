# ==================== app.py ====================
import streamlit as st
import docx
import re
from io import BytesIO
from datetime import datetime
import dashscope
from dashscope import Generation

# 页面配置
st.set_page_config(page_title="《下一站》剪辑稿生成器", layout="wide")

# 标题
st.title("🎬 《下一站》剪辑稿智能生成系统")
st.markdown("---")

# 初始化会话状态
if 'field_notes_lines' not in st.session_state:
    st.session_state.field_notes_lines = []
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📖 使用说明")
    st.write("1. 上传场记稿文件")
    st.write("2. 在原文上勾选需要保留的内容")
    st.write("3. 添加分段，AI自动生成OS建议")
    st.write("4. 生成并下载两个文档")
    
    st.header("📋 格式规范")
    st.write("- OS旁白：`OS：内容//`")
    st.write("- 实况对话：`内容//` (自动添加)")
    st.write("- 同一段内不换行，连续排列")
    st.write("- 分段时换行，用OS衔接")
    
    st.header("⚙️ AI设置")
    api_key_input = st.text_input("通义千问API Key", type="password", value=st.session_state.api_key)
    if api_key_input:
        st.session_state.api_key = api_key_input
        dashscope.api_key = api_key_input

# ==================== 第1步：上传场记稿 ====================
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
    
    # 按行分割（每行一个可标记单元）
    lines = field_notes_text.split('\n')
    st.session_state.field_notes_lines = lines
    
    with st.expander("📋 场记稿预览"):
        st.text_area("原始内容", field_notes_text, height=200)

# ==================== 第2步：高光标记 ====================
st.header("✏️ 第2步：高光标记（直接在原稿上勾选）")

if st.session_state.field_notes_lines:
    st.write("✅ 勾选需要保留到剪辑稿的内容，系统会自动添加'//'标记")
    
    # 创建可勾选的列表
    selected_indices = []
    
    for i, line in enumerate(st.session_state.field_notes_lines):
        if line.strip():
            # 每行一个复选框
            if st.checkbox(line, key=f"line_{i}"):
                selected_indices.append(i)
    
    st.write(f"已选择 {len(selected_indices)} 段内容")
    
    # 存储选中的内容
    st.session_state.selected_indices = selected_indices

# ==================== 第3步：分段管理 ====================
st.header("📑 第3步：分段管理")

if 'selected_indices' in st.session_state and st.session_state.selected_indices:
    # 获取选中的内容
    selected_contents = [st.session_state.field_notes_lines[i] for i in st.session_state.selected_indices]
    
    # 手动添加分段
    col_seg1, col_seg2 = st.columns([3, 1])
    with col_seg1:
        new_segment_name = st.text_input("新分段名称（地点/主题）", placeholder="如：咖啡巴士引入/红枫林观景")
    with col_seg2:
        if st.button("➕ 添加分段"):
            if new_segment_name:
                st.session_state.segments.append({
                    "name": new_segment_name,
                    "content_indices": [],
                    "os_suggestion": "",
                    "os_custom": ""
                })
                st.success(f"已添加分段：{new_segment_name}")
    
    # 显示分段
    if st.session_state.segments:
        st.subheader("当前分段")
        for i, seg in enumerate(st.session_state.segments):
            with st.expander(f"分段{i+1}: {seg['name']}", expanded=True):
                # 分配素材到分段
                st.write("分配选中的内容到此分段：")
                for j, idx in enumerate(st.session_state.selected_indices):
                    content = st.session_state.field_notes_lines[idx]
                    if st.checkbox(f"{j+1}. {content[:60]}...", key=f"seg_{i}_item_{j}"):
                        if idx not in seg['content_indices']:
                            seg['content_indices'].append(idx)
                
                # AI生成OS建议
                st.write("**OS建议（探访人视角）**")
                use_ai = st.checkbox("使用AI生成OS建议", key=f"ai_{i}")
                
                if use_ai and st.session_state.api_key:
                    if st.button("🤖 生成OS建议", key=f"gen_os_{i}"):
                        # 获取此分段的内容
                        seg_contents = [st.session_state.field_notes_lines[idx] for idx in seg['content_indices']]
                        context = "\n".join(seg_contents[:5])  # 取前5段作为上下文
                        
                        # 调用通义千问API
                        prompt = f"""你是《下一站》电视节目编导，请根据以下采访内容，写一句探访人视角的OS旁白。
要求：
1. 以第一人称"我"的角度
2. 可以是现场情感表达或补充说明
3. 简洁有力，30字以内
4. 用于衔接上下两段内容

采访内容：
{context}

请直接输出OS内容，不要其他说明："""
                        
                        try:
                            response = Generation.call(
                                model='qwen-turbo',
                                prompt=prompt
                            )
                            if response.status_code == 200:
                                seg['os_suggestion'] = response.output.text.strip()
                                st.success("OS建议已生成！")
                        except Exception as e:
                            st.error(f"AI生成失败：{str(e)}")
                    elif seg['os_suggestion']:
                        st.info(f"AI建议：{seg['os_suggestion']}")
                elif use_ai and not st.session_state.api_key:
                    st.warning("请先在侧边栏输入通义千问API Key")
                
                # 手动编辑OS
                os_custom = st.text_area("OS旁白（可编辑）", seg['os_custom'], height=60, 
                                        placeholder="如：边喝咖啡，边欣赏沿路美景...", key=f"os_custom_{i}")
                seg['os_custom'] = os_custom
                
                # 删除分段
                if st.button(f"删除此分段", key=f"del_seg_{i}"):
                    st.session_state.segments.pop(i)
                    st.rerun()
    else:
        st.info("请先添加分段，然后将内容分配到各分段")

# ==================== 第4步：预览和导出 ====================
st.header("💾 第4步：预览和导出")

if st.button("📝 生成剪辑稿预览"):
    if 'segments' in st.session_state and st.session_state.segments:
        # 生成剪辑稿内容
        edit_script = ""
        
        for seg_idx, seg in enumerate(st.session_state.segments):
            # 添加分段标题
            edit_script += f"【分段{seg_idx+1}: {seg['name']}】\n"
            
            # 添加OS（优先使用手动编辑的，其次使用AI建议）
            os_text = seg['os_custom'] if seg['os_custom'] else seg['os_suggestion']
            if os_text:
                edit_script += f"OS：{os_text}//\n"
            
            # 添加实况内容（同一段内不换行，连续排列）
            segment_content = ""
            for idx in seg['content_indices']:
                content = st.session_state.field_notes_lines[idx].strip()
                if content:
                    # 自动添加//标记，不换行
                    segment_content += f"{content}// "
            
            if segment_content:
                edit_script += f"{segment_content}\n"
            
            edit_script += "\n" + "="*50 + "\n\n"
        
        st.session_state.edit_script_preview = edit_script
        
        # 显示预览
        st.subheader("剪辑稿预览")
        st.text_area("预览内容", edit_script, height=400)
    else:
        st.warning("请先添加分段并分配内容")

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
        if uploaded_file and 'selected_indices' in st.session_state:
            # 创建标记后的场记稿
            doc = docx.Document()
            doc.add_heading('《下一站》场记稿（已标记）', 0)
            doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            doc.add_paragraph(f"已标记内容数量：{len(st.session_state.selected_indices)}\n")
            
            # 添加原始内容，高亮标记部分
            doc.add_heading('原始场记稿（✅=已标记）', level=1)
            for i, line in enumerate(st.session_state.field_notes_lines):
                if line.strip():
                    if i in st.session_state.selected_indices:
                        p = doc.add_paragraph()
                        runner = p.add_run(f"✅ {line}")
                        runner.font.highlight_color = docx.enum.text.WD_COLOR_INDEX.YELLOW
                    else:
                        doc.add_paragraph(line)
            
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
            st.warning("请先上传场记稿并标记内容")

# 页脚
st.markdown("---")
st.caption("《下一站》节目组内部工具 | 版本 3.0 | 满足4大更正需求")
# ==================== 代码结束 ====================
