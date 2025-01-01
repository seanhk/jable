import os
import random
from typing import Union
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import ssl
import certifi

# 使用自定义的 SSL 上下文确保安全连接
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(cafile=certifi.where())

requests.adapters.DEFAULT_RETRIES = 5

app = FastAPI()

# 跨域处理
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_random_line(file_path: str) -> str:
    """从文件中读取一行随机 URL"""
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, 'r') as file:
        lines = file.readlines()

    if not lines:
        raise HTTPException(status_code=400, detail="File is empty")

    return random.choice(lines).strip()

def fetch_m3u8_from_website(url: str) -> str:
    """从指定网站动态获取 m3u8 URL"""
    try:
        response = requests.get(url, verify=certifi.where(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 假设 m3u8 地址存放在 <video> 标签的 src 属性中
        video_tag = soup.find("video")
        if video_tag and video_tag.get("src"):
            m3u8_url = video_tag["src"]

            # 如果是 blob 地址，可能需要进一步解析或处理
            if m3u8_url.startswith("blob:"):
                raise HTTPException(status_code=400, detail="Blob URLs are not directly accessible")
            return m3u8_url
        else:
            raise HTTPException(status_code=404, detail="No m3u8 URL found on the page")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching m3u8: {str(e)}")

@app.get("/")
async def get_video_url(source: str = "file", website_url: Union[str, None] = None):
    """
    根据 source 参数返回视频 URL:
    - "file": 从文件中读取随机 URL
    - "website": 从指定网站动态获取 m3u8 URL
    """
    if source == "file":
        # 从文件中读取随机 URL
        file_path = "./video_urls.txt"
        try:
            random_line = read_random_line(file_path)
            return {"url": random_line}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif source == "website":
        # 确保提供了目标网站 URL
        if not website_url:
            raise HTTPException(status_code=400, detail="website_url parameter is required")
        
        # 动态解析 m3u8 地址
        try:
            m3u8_url = fetch_m3u8_from_website(website_url)
            return {"url": m3u8_url}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid source parameter")
