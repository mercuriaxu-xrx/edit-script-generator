# ==================== app.py ====================
import streamlit as st
import docx
import re
from io import BytesIO

# 页面配置
st.set_page_config(page_title="《下一站》剪辑稿生成器", layout="wide")

# 标题
st.title("🎬 《下一站》剪辑稿生成系统")
st.markdown("---")

# 侧边栏 - 使用说明
with st.sidebar:
    st.header("📖 使用说明")
    st.write("1. 上传场记稿文件")
    st.write("2. 在预览区选中需要的内容")
    st.write("3. 点击'标记选中内容'")
    st.write("4. 在编辑区添加OS和空镜说明")
    st.write("5. 点击'生成剪辑稿'下载")
    
    st.header("📋 格式规范")
    st.write("- OS旁白：`OS：内容//`")
    st.write("- 实况对话：`内容//`")
    st.write("- 空镜说明：`【空镜说明】`")
    st.write("- 剪辑点：`//`")

# 初始化会话状态
if 'selected_clips' not in st.session_state:
    st.session_state.selected_clips = []
if 'edit_script' not in st.session_state:
    st.session_state.edit_script = ""

# 主界面 - 两列布局
col1, col2 = st.columns([1, 1])

# ==================== 左侧：场记稿处理 ====================
with col1:
    st.header("📄 场记稿处理")
    
    # 文件上传
    uploaded_file = st.file_uploader("上传场记稿(.docx)", type=["docx"])
    
    if uploaded_file:
        # 读取文档
        doc = docx.Document(uploaded_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        field_notes_text = "\n".join(full_text)
        
        # 显示场记稿预览
        st.subheader("场记稿预览")
        st.text_area("原始内容", field_notes_text, height=400, key="field_notes")
        
        # 标记功能
        st.subheader("标记需要的内容")
        selected_text = st.text_area("选中要保留的内容（复制粘贴到这里）", height=100, key="selected_text")
        
        timecode = st.text_input("时间码（可选）", placeholder="如：3:59")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ 标记选中内容", use_container_width=True):
                if selected_text:
                    clip = {
                        "content": selected_text,
                        "timecode": timecode,
                        "type": "实况"
                    }
                    st.session_state.selected_clips.append(clip)
                    st.success(f"已添加！当前共 {len(st.session_state.selected_clips)} 段素材")
        
        with col_btn2:
            if st.button("🗑️ 清空所有标记", use_container_width=True):
                st.session_state.selected_clips = []
                st.success("已清空")
        
        # 显示已标记素材
        st.subheader("📦 已标记素材库")
        if st.session_state.selected_clips:
            for i, clip in enumerate(st.session_state.selected_clips):
                with st.expander(f"素材{i+1} {clip['timecode'] or '无时间码'}"):
                    st.write(f"**类型:** {clip['type']}")
                    st.write(f"**内容:** {clip['content']}")
                    if st.button(f"删除", key=f"del_{i}"):
                        st.session_state.selected_clips.pop(i)
                        st.rerun()
        else:
            st.info("暂无标记素材，请在上方添加")

# ==================== 右侧：剪辑稿编辑 ====================
with col2:
    st.header("✂️ 剪辑稿编辑")
    
    # OS旁白输入
    st.subheader("添加OS旁白")
    os_input = st.text_area("OS内容", placeholder="输入主持人旁白内容...", height=80, key="os_input")
    
    if st.button("➕ 添加OS", use_container_width=True):
        if os_input:
            os_clip = {
                "content": os_input,
                "timecode": None,
                "type": "OS"
            }
            st.session_state.selected_clips.append(os_clip)
            st.success("OS已添加")
    
    # 空镜说明
    st.subheader("添加空镜说明")
    broll_templates = [
        "【航拍转场】",
        "【唯美景色空镜】",
        "【人物特写】",
        "【环境空镜】",
        "【快速剪辑】",
        "【自定义...】"
    ]
    broll_select = st.selectbox("选择模板", broll_templates, key="broll_select")
    
    if broll_select == "【自定义...】":
        broll_custom = st.text_input("输入空镜说明", placeholder="如：【fu大爷换装快速剪辑】")
        if st.button("➕ 添加空镜", use_container_width=True):
            if broll_custom:
                broll_clip = {
                    "content": broll_custom,
                    "timecode": None,
                    "type": "空镜"
                }
                st.session_state.selected_clips.append(broll_clip)
                st.success("空镜已添加")
    else:
        if st.button("➕ 添加空镜", use_container_width=True):
            broll_clip = {
                "content": broll_select,
                "timecode": None,
                "type": "空镜"
            }
            st.session_state.selected_clips.append(broll_clip)
            st.success("空镜已添加")
    
    # 剪辑稿预览
    st.subheader("📝 剪辑稿预览")
    
    # 生成预览
    preview_text = ""
    for clip in st.session_state.selected_clips:
        if clip["type"] == "OS":
            preview_text += f"OS：{clip['content']}//\n\n"
        elif clip["type"] == "空镜":
            preview_text += f"{clip['content']}\n\n"
        else:
            timecode_str = f"{clip['timecode']} " if clip['timecode'] else ""
            preview_text += f"{timecode_str}{clip['content']}//\n\n"
    
    st.session_state.edit_script = preview_text
    st.text_area("预览", preview_text, height=300, key="preview")
    
    # 调整顺序
    st.subheader("🔄 调整顺序")
    if len(st.session_state.selected_clips) > 1:
        col_up, col_down = st.columns(2)
        with col_up:
            if st.button("⬆️ 上移选中项", use_container_width=True):
                # 简单实现：交换最后两项
                if len(st.session_state.selected_clips) >= 2:
                    st.session_state.selected_clips[-1], st.session_state.selected_clips[-2] = \
                    st.session_state.selected_clips[-2], st.session_state.selected_clips[-1]
                    st.rerun()
        with col_down:
            if st.button("⬇️ 下移选中项", use_container_width=True):
                if len(st.session_state.selected_clips) >= 2:
                    st.session_state.selected_clips[-1], st.session_state.selected_clips[-2] = \
                    st.session_state.selected_clips[-2], st.session_state.selected_clips[-1]
                    st.rerun()
    
    # 导出
    st.subheader("💾 导出剪辑稿")
    
    if st.button("📥 生成并下载剪辑稿", type="primary", use_container_width=True):
        if st.session_state.edit_script:
            # 创建Word文档
            doc = docx.Document()
            doc.add_heading('《下一站》剪辑稿', 0)
            doc.add_paragraph(st.session_state.edit_script)
            
            # 保存到内存
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            # 提供下载
            st.download_button(
                label="点击下载剪辑稿(.docx)",
                data=buffer,
                file_name="剪辑稿_生成.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("请先添加内容再生成")

# 页脚
st.markdown("---")
st.caption("《下一站》节目组内部工具 | 版本 1.0")
# ==================== 代码结束 ====================