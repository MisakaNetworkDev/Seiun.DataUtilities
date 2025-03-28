import json

import requests

def upload_article_img(file_path: str, token: str, base_url: str = "https://example.com"):
    """
    上传文章图片到 Seiun API。

    :param file_path: 图片文件的相对路径
    :param token: 认证 Token
    :param base_url: API 基础 URL，默认为 https://example.com
    :return: API 响应 JSON 数据
    """
    url = f"{base_url}/api/article/upload-img"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    with open(file_path, "rb") as file:
        files = {"articleImgFile": file}
        response = requests.post(url, headers=headers, files=files)

    return response.json()


def create_article(article: str, title: str, desc: str, image_names: list[str] = None, cover_file_name: str = None, token: str = "",
                   base_url: str = "https://example.com"):
    """
    创建文章并提交到 Seiun API。

    :param article: 文章内容（必填）
    :param image_names: 文章内包含的图片文件名列表（可选）
    :param cover_file_name: 文章封面文件名（可选）
    :param token: 认证 Token
    :param base_url: API 基础 URL，默认为 https://example.com
    :return: API 响应 JSON 数据
    """
    url = f"{base_url}/api/article/create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "content": article,
        "title": title,
        "description": desc,
        "image_names": image_names or [],
        "cover_file_name": cover_file_name,
        "vocabulary": None
    }

    response = requests.post(url, headers=headers, json=payload)

    return response.json()

if __name__ == "__main__":
    BASE_URL = "http://localhost:5222"
    TOKEN = requests.post(f'{BASE_URL}/api/user/login', json={
      "user_name": "User_CGTN",
      "password": "Ab123456"
    }).json()["data"]["token"]

    with open("data/posts/posts.json", "r") as file:
        posts = json.load(file)
        for post in posts:
            file_path = "data/posts/" + post["cover"]
            response = upload_article_img(file_path, TOKEN, BASE_URL)
            print(response)
            post["cover_file"] = response["data"]["article_img_name"]

        for post in posts:
            with open(f"data/posts/{post['file']}", "r") as file:
                post["content"] = file.read()
            response = create_article(post["content"], post["title"], post["desc"], None, post["cover_file"], TOKEN, BASE_URL)
            print(response)
