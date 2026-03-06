import streamlit as st
import time
import io
from core_modules import video_downloader

# ==========================================
# 🥇 页面配置
# ==========================================
st.set_page_config(page_title="Video Downloader --jxyuan", layout="centered")

# ==========================================
# 1. 深度定制 CSS (保持你的高级感)
# ==========================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 10vh !important; max-width: 750px !important; }
    .custom-label { display: flex; align-items: center; height: 40px; font-size: 16px; font-weight: 500; color: #E0E0E0; }
    .custom-label-radio { display: flex; align-items: flex-start; padding-top: 8px; font-size: 16px; font-weight: 500; color: #E0E0E0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 初始化状态
# ==========================================
if 'formats' not in st.session_state: st.session_state['formats'] = None
if 'selected_format_id' not in st.session_state: st.session_state['selected_format_id'] = None

# ==========================================
# 3. UI 布局
# ==========================================
st.markdown("<h1 style='text-align: center; color: #FFFFFF; font-weight: normal; margin-bottom: 40px;'>Video Downloader --jxyuan</h1>", unsafe_allow_html=True)
st.divider()

col_left, col_right = 1.2, 3.5

# --- 第一行：输入与解析 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label'>请输入视频网址</div>", unsafe_allow_html=True)
with c2:
    i_col, b_col = st.columns([3, 1])
    url_input = i_col.text_input("", placeholder="在此粘贴链接...", label_visibility="collapsed")
    if b_col.button("解析", use_container_width=True):
        if url_input:
            with st.spinner("解析中..."):
                try:
                    st.session_state['formats'] = video_downloader.get_video_formats(url_input)
                    st.toast("解析成功！")
                except: st.toast("解析失败", icon="❌")

# --- 第二行：清晰度选择 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label-radio'>支持清晰度</div>", unsafe_allow_html=True)
with c2:
    if st.session_state['formats']:
        options = [f.get('resolution', '默认画质') for f in st.session_state['formats']]
        sel = st.radio("", options, label_visibility="collapsed")
        st.session_state['selected_format_id'] = next(f['id'] for f in st.session_state['formats'] if f['resolution'] == sel)
    else:
        st.markdown("<div style='color: #666; padding-top:8px;'>等待解析...</div>", unsafe_allow_html=True)

st.divider()

# --- 第三行：执行下载并提供下载按钮 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label'>保存视频</div>", unsafe_allow_html=True)
with c2:
    if st.button("准备下载数据 (生成 MP4)", type="primary", use_container_width=True):
        if not url_input or not st.session_state['selected_format_id']:
            st.error("请先解析链接并选择清晰度")
        else:
            with st.spinner("正在从服务器抓取并转换，请稍候..."):
                try:
                    # 关键修改：下载到服务器的临时文件，然后读取为 Bytes
                    temp_file = f"temp_{int(time.time())}.mp4"
                    video_downloader.download_video(url_input, st.session_state['selected_format_id'], temp_file)
                    
                    with open(temp_file, "rb") as f:
                        video_bytes = f.read()
                    
                    # 提供下载按钮给浏览器
                    st.download_button(
                        label="💾 点击这里保存到本地",
                        data=video_bytes,
                        file_name=f"video_{int(time.time())}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"下载失败: {e}")