import os

# 1. C盘一键清理规则
SYSTEM_CLEAN_CONFIG = [
    {"id": "win_temp", "name": "Windows 系统临时文件", "icon": "📁", "paths": [r"C:\Windows\Temp"], "default": True},
    {"id": "user_temp", "name": "当前用户缓存文件", "icon": "📂", "paths": [os.environ.get('TEMP', 'C:\\Temp')], "default": True},
    {"id": "prefetch", "name": "系统预读与加速缓存", "icon": "⚡", "paths": [r"C:\Windows\Prefetch"], "default": True},
    {"id": "recycle", "name": "系统回收站残留", "icon": "🗑️", "paths": [r"C:\$Recycle.Bin"], "default": True},
    {"id": "update", "name": "Windows 更新补丁包", "icon": "🔄", "paths": [r"C:\Windows\SoftwareDistribution\Download"], "default": False},
    {"id": "logs", "name": "系统运行诊断日志", "icon": "📝", "paths": [r"C:\Windows\Logs"], "default": False}
]

# 2. 专项清理：社交与媒体软件
APP_GROUPS = {
    "💬 社交办公": [
        {"name": "微信 (WeChat)", "paths": [os.path.expandvars(r"%USERPROFILE%\Documents\WeChat Files")]},
        {"name": "企业微信 (WXWork)", "paths": [os.path.expandvars(r"%USERPROFILE%\Documents\WXWork")]},
        {"name": "QQ", "paths": [os.path.expandvars(r"%USERPROFILE%\Documents\Tencent Files")]},
        {"name": "钉钉 (DingTalk)", "paths": [os.path.expandvars(r"%APPDATA%\DingTalk")]}
    ],
    "🎬 视频媒体": [
        {"name": "爱奇艺 (iQIYI)", "paths": [r"C:\QiYiVideo\Cache", os.path.expandvars(r"%LOCALAPPDATA%\Packages\爱奇艺_*\LocalCache")]},
        {"name": "腾讯视频 (TencentVideo)", "paths": [os.path.expandvars(r"%LOCALAPPDATA%\Tencent\TXVideo\Cache")]},
        {"name": "优酷 (Youku)", "paths": [r"C:\YoukuFiles\download", os.path.expandvars(r"%LOCALAPPDATA%\Youku\Cache")]},
        {"name": "哔哩哔哩 (Bilibili)", "paths": [os.path.expandvars(r"%LOCALAPPDATA%\Packages\bilibili_*\LocalCache")]}
    ]
}