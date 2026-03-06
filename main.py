import streamlit as st
import time
import io
import os
import re
import yt_dlp

# ==========================================
# 🥇 页面配置 (必须是第一行 st 命令)
# ==========================================
st.set_page_config(page_title="Video Downloader --jxyuan", layout="centered")

# ==========================================
# 1. 核心后台逻辑 (整合进主文件，确保调用的是最新逻辑)
# ==========================================

def clean_url(input_text):
    """提取纯净网址：支持处理带中文的分享文案和弹窗链接"""
    # 使用正则从乱七八糟的文案中抠出 http 链接
    url_match = re.search(r'(https?://[^\s]+)', input_text)
    url = url_match.group(1) if url_match else input_text
    url = url.strip()
    
    # 修复抖音弹窗链接
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match:
            url = f"https://www.douyin.com/video/{match.group(1)}"
    return url

def get_formats_logic(url):
    """解析视频信息"""
    target_url = clean_url(url)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10, # 设置10秒超时，防止死等
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target_url, download=False)
        formats = info.get('formats', [])
        
        if not formats:
            return [{'id': 'best', 'resolution': '最佳画质 (自动选择)', 'height': 9999}]
        
        processed_formats = []
        for f in formats:
            if f.get('vcodec') == 'none': continue # 跳过纯音频
            
            res = f"{f.get('width','?')}x{f.get('height','?')}P" if f.get('width') else f"默认画质({f.get('format_id')})"
            processed_formats.append({
                'id': f.get('format_id'),
                'resolution': res,
                'height': f.get('height', 0)
            })
            
    # 去重并排序
    unique = {x['resolution']: x for x in processed_formats}.values()
    return sorted(list(unique), key=lambda x: x['height'], reverse=True)

def download_logic(url, format_id, output_path):
    """下载并混流"""
    target_url = clean_url(url)
    # 智能混流：画面 + 最佳音频
    smart_format = f"{format_id}+bestaudio/best" if format_id != 'best' else 'best'
    
    ydl_opts = {
        'format': smart_format,
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])
    except:
        # 安全气囊：降级下载
        ydl_opts['format'] = format_id
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])
    return output_path

# ==========================================
# 2. 深度定制 CSS
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
# 3. 初始化状态与 UI
# ==========================================
if 'formats' not in st.session_state: st.session_state['formats'] = None
if 'selected_format_id' not in st.session_state: st.session_state['selected_format_id'] = None

st.markdown("<h1 style='text-align: center; color: #FFFFFF; font-weight: normal; margin-bottom: 40px;'>Video Downloader --jxyuan</h1>", unsafe_allow_html=True)
st.divider()

col_left, col_right = 1.2, 3.5

# --- 第一行：输入与解析 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label'>请输入视频网址</div>", unsafe_allow_html=True)
with c2:
    i_col, b_col = st.columns([3, 1])
    url_input = i_col.text_input("", placeholder="在此粘贴链接或分享文案...", label_visibility="collapsed")
    if b_col.button("解析", use_container_width=True):
        if url_input:
            with st.spinner("解析中..."):
                try:
                    # 直接调用本地函数，不再通过 video_downloader 模块
                    st.session_state['formats'] = get_formats_logic(url_input)
                    st.toast("解析成功！")
                except Exception as e:
                    st.toast(f"解析失败: {str(e)[:20]}...", icon="❌")

# --- 第二行：清晰度选择 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label-radio'>支持清晰度</div>", unsafe_allow_html=True)
with c2:
    if st.session_state['formats']:
        options = [f['resolution'] for f in st.session_state['formats']]
        sel = st.radio("", options, label_visibility="collapsed")
        st.session_state['selected_format_id'] = next(f['id'] for f in st.session_state['formats'] if f['resolution'] == sel)
    else:
        st.markdown("<div style='color: #666; padding-top:8px;'>等待解析...</div>", unsafe_allow_html=True)

st.divider()

# --- 第三行：执行下载 ---
c1, c2 = st.columns([col_left, col_right])
with c1: st.markdown("<div class='custom-label'>下载视频</div>", unsafe_allow_html=True)
with c2:
    if st.button("生成下载链接", type="primary", use_container_width=True):
        if not url_input or not st.session_state['selected_format_id']:
            st.error("请先解析链接并选择清晰度")
        else:
            with st.spinner("正在从服务器转取..."):
                try:
                    temp_file = f"temp_video_{int(time.time())}.mp4"
                    download_logic(url_input, st.session_state['selected_format_id'], temp_file)
                    
                    with open(temp_file, "rb") as f:
                        video_bytes = f.read()
                    
                    st.download_button(
                        label="💾 准备就绪！点击保存到本地",
                        data=video_bytes,
                        file_name=f"video_{int(time.time())}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    st.balloons()
                    os.remove(temp_file) # 清理服务器空间
                except Exception as e:
                    st.error(f"下载失败: {e}")
