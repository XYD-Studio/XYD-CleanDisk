import os

# 1. 核心系统瘦身：仅包含 100% 安全的可删系统级垃圾
SYSTEM_CLEAN_CONFIG = [
    {"id": "win_temp", "name": "Windows 系统临时文件", "icon": "📁", "paths": [r"C:\Windows\Temp"], "default": True},
    {"id": "user_temp", "name": "当前用户缓存文件", "icon": "📂", "paths": [os.environ.get('TEMP', 'C:\\Temp')], "default": True},
    {"id": "prefetch", "name": "系统预读与加速缓存", "icon": "⚡", "paths": [r"C:\Windows\Prefetch"], "default": True},
    {"id": "recycle", "name": "系统回收站残留", "icon": "🗑️", "paths": [r"C:\$Recycle.Bin"], "default": True},
    {"id": "update", "name": "Windows 更新补丁包", "icon": "🔄", "paths": [r"C:\Windows\SoftwareDistribution\Download"], "default": False},
    {"id": "logs", "name": "系统运行诊断日志", "icon": "📝", "paths": [r"C:\Windows\Logs"], "default": False}
]

# 2. 专项深度清理：精确到子目录，保护聊天记录(db)和账号数据，绝对安全！
user_profile = os.environ.get('USERPROFILE', '')
local_appdata = os.environ.get('LOCALAPPDATA', '')

APP_GROUPS = {
    "💬 社交与办公": [
        {"name": "微信 (缓存/图片/视频/接收文件)", "paths": [
            os.path.join(user_profile, r"Documents\WeChat Files\FileStorage\Cache"),
            os.path.join(user_profile, r"Documents\WeChat Files\FileStorage\Video"),
            os.path.join(user_profile, r"Documents\WeChat Files\FileStorage\Image"),
            os.path.join(user_profile, r"Documents\WeChat Files\FileStorage\File")
        ]},
        {"name": "QQ (图片/缓存/短视频)", "paths": [
            os.path.join(user_profile, r"Documents\Tencent Files\Image"),
            os.path.join(user_profile, r"Documents\Tencent Files\Video")
        ]},
        {"name": "企业微信 (WXWork 缓存区)", "paths": [
            os.path.join(user_profile, r"Documents\WXWork\Data\Cache"),
            os.path.join(user_profile, r"Documents\WXWork\Data\Image")
        ]},
        {"name": "钉钉 (DingTalk 临时数据)", "paths": [
            os.path.join(os.environ.get('APPDATA', ''), r"DingTalk\Cache")
        ]}
    ],
    "🎬 视频媒体": [
        {"name": "爱奇艺 (iQIYI 播放缓存)", "paths": [r"C:\QiYiVideo\Cache", os.path.join(local_appdata, r"Packages\爱奇艺\LocalCache")]},
        {"name": "腾讯视频 (TXVideo 缓存)", "paths": [os.path.join(local_appdata, r"Tencent\TXVideo\Cache")]},
        {"name": "优酷 (Youku 下载片段)", "paths": [r"C:\YoukuFiles\download", os.path.join(local_appdata, r"Youku\Cache")]},
        {"name": "哔哩哔哩 (Bilibili 本地缓存)", "paths": [os.path.join(local_appdata, r"Packages\bilibili\LocalCache")]}
    ]
}