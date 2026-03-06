import yt_dlp
import os
import re

def clean_url(url):
    """
    极简链接处理：只处理真正会导致解析崩溃的特殊链接
    """
    # 抖音的弹窗链接依然需要处理，否则 yt-dlp 不认
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match:
            return f"https://www.douyin.com/video/{match.group(1)}"
            
    # B站等其他平台的链接，原封不动交给 yt-dlp 原生解析，不画蛇添足
    return url

def get_video_formats(url):
    clean_video_url = clean_url(url)
    
    # 极简配置：去掉了干扰原始提取器的自定义 Header
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    formats_list = []
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_video_url, download=False)
        formats = info.get('formats', [])
        
        if not formats:
            return [{'id': 'best', 'resolution': '最佳画质 (自动选择)', 'height': 9999}]
        
        for f in formats:
            format_id = f.get('format_id')
            vcodec = f.get('vcodec')
            
            # 过滤掉纯音频
            if vcodec == 'none':
                continue
                
            width = f.get('width')
            height = f.get('height')
            
            if width and height:
                res_str = f"{width}x{height}P"
                sort_key = height
            else:
                res_str = f"默认画质 (ID: {format_id})"
                sort_key = 0
                
            formats_list.append({
                'id': format_id,
                'resolution': res_str,
                'height': sort_key
            })
                
    unique_formats = {}
    for fmt in formats_list:
        if fmt['resolution'] not in unique_formats:
            unique_formats[fmt['resolution']] = fmt
            
    result = list(unique_formats.values())
    result.sort(key=lambda x: x['height'], reverse=True)
    
    if not result:
         return [{'id': 'best', 'resolution': '最佳画质 (自动选择)', 'height': 9999}]
        
    return result

def download_video(url, format_id, output_path):
    clean_video_url = clean_url(url)
    
    if os.path.exists(output_path):
        os.remove(output_path)
        
    # 智能混流尝试：画面 + 最佳音频
    smart_format = f"{format_id}+bestaudio/best" if format_id != 'best' else 'best'

    ydl_opts = {
        'format': smart_format,
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4'
    }
    
    try:
        # 第一套方案：尝试画面+音频的完美混流 (适合 1080P DASH流)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_video_url])
    except Exception as e:
        # 第二套方案 (安全气囊)：如果 B 站的某个清晰度本来就自带声音，
        # 强制加 +bestaudio 会导致报错。如果报错，立刻回退到最原始的 format_id 下载。
        print(f"尝试混流遇到阻碍，启用基础下载模式...")
        ydl_opts['format'] = format_id
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_video_url])
        
    if not os.path.exists(output_path):
        raise FileNotFoundError("后台下载失败，未能生成视频文件。")
        
    return output_path