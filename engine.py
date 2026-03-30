import os
import math
import hashlib
import string
import ctypes
from PySide6.QtCore import QThread, Signal


class FileEngine:
    @staticmethod
    def format_size(size_bytes):
        if size_bytes <= 0: return "0 B"
        units = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        return f"{round(size_bytes / math.pow(1024, i), 2)} {units[i]}"

    @staticmethod
    def get_physical_size(file_path):
        """
        【商业级黑科技】：穿透稀疏文件与压缩文件，获取真正的“占用空间 (Size on Disk)”
        """
        try:
            high = ctypes.c_uint32(0)
            # 调用 Windows Kernel32 底层 API 获取真实物理占用大小
            low = ctypes.windll.kernel32.GetCompressedFileSizeW(str(file_path), ctypes.byref(high))

            # 如果返回值是全F，且存在错误码，说明 API 调用失败，退回到逻辑大小
            if low == 0xFFFFFFFF:
                err = ctypes.GetLastError()
                if err != 0:
                    return os.path.getsize(file_path)

            # 将高位和低位拼接成最终的真实字节数
            return (high.value << 32) + low
        except:
            # 遇到权限受限等异常情况，安全退回到标准的逻辑大小
            return os.path.getsize(file_path)

    @staticmethod
    def get_md5(file_path):
        m = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                m.update(f.read(1024 * 1024))
            return m.hexdigest()
        except:
            return None

    @staticmethod
    def get_all_drives():
        return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]


class ScanWorker(QThread):
    progress_msg = Signal(str)
    result_data = Signal(dict)
    finished_scan = Signal()

    def __init__(self, mode="system", threshold_bytes=104857600):
        super().__init__()
        self.mode = mode
        self.threshold_bytes = threshold_bytes  # 动态接收用户设置的阈值

    def run(self):
        if self.mode == "system":
            self._scan_system()
        elif self.mode == "apps":
            self._scan_apps()
        elif self.mode == "large":
            self._scan_large()
        elif self.mode == "duplicate":
            self._scan_duplicate()
        self.finished_scan.emit()

    def _scan_system(self):
        from config import SYSTEM_CLEAN_CONFIG
        for item in SYSTEM_CLEAN_CONFIG:
            self.progress_msg.emit(f"正在扫描: {item['name']}")
            total_size = 0
            for path in item['paths']:
                if not os.path.exists(path): continue
                for root, _, files in os.walk(path):
                    for f in files:
                        try:
                            total_size += FileEngine.get_physical_size(os.path.join(root, f))
                        except:
                            pass
            self.result_data.emit({"type": "system", "id": item["id"], "size": total_size})

    def _scan_apps(self):
        from config import APP_GROUPS
        for cat_name, apps in APP_GROUPS.items():
            for app in apps:
                self.progress_msg.emit(f"正在分析: {app['name']}")
                files_found = []
                for p in app['paths']:
                    if not os.path.exists(p): continue
                    for root, _, files in os.walk(p):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                stat = os.stat(fp)
                                files_found.append(
                                    {"name": f, "path": fp, "size": stat.st_size, "mtime": stat.st_mtime})
                            except:
                                continue
                if files_found:
                    self.result_data.emit(
                        {"type": "app", "category": cat_name, "app_name": app['name'], "files": files_found})

    def _scan_large(self):
        for drive in FileEngine.get_all_drives():
            self.progress_msg.emit(f"正在全盘检索大文件: {drive}")
            for root, _, files in os.walk(drive):
                if any(x in root for x in ["C:\\Windows", "$Recycle.Bin", "Program Files"]): continue
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = FileEngine.get_physical_size(fp)
                        if sz >= self.threshold_bytes:
                            self.result_data.emit(
                                {"type": "large", "path": fp, "size": sz, "mtime": os.path.getmtime(fp)})
                    except:
                        continue

    def _scan_duplicate(self):
        size_map = {}
        for drive in FileEngine.get_all_drives():
            self.progress_msg.emit(f"重复文件扫描阶段 1/2 (按大小筛选): {drive}")
            for root, _, files in os.walk(drive):
                if "Windows" in root: continue
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = FileEngine.get_physical_size(fp)
                        if sz >= self.threshold_bytes:
                            if sz not in size_map: size_map[sz] = []
                            size_map[sz].append(fp)
                    except:
                        continue

        self.progress_msg.emit("重复文件扫描阶段 2/2: 正在进行特征码 MD5 校验...")
        for sz, paths in size_map.items():
            if len(paths) < 2: continue
            md5_map = {}
            for p in paths:
                md5 = FileEngine.get_md5(p)
                if md5:
                    if md5 not in md5_map: md5_map[md5] = []
                    md5_map[md5].append(p)

            for md5, dup_paths in md5_map.items():
                if len(dup_paths) > 1:
                    self.result_data.emit({"type": "duplicate", "size": sz, "paths": dup_paths})