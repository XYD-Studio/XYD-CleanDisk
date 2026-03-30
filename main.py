import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTreeWidget,
                               QTreeWidgetItem, QStackedWidget, QHeaderView, QFrame,
                               QMessageBox, QMenu, QSpinBox, QComboBox, QScrollArea)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtGui import QFont, QIcon, QCursor, QPixmap

from config import SYSTEM_CLEAN_CONFIG
from engine import FileEngine, ScanWorker


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SafeSortItem(QTreeWidgetItem):
    def __lt__(self, other):
        col = self.treeWidget().sortColumn()
        val1 = self.data(col, Qt.UserRole)
        val2 = other.data(col, Qt.UserRole)
        if val1 is not None and val2 is not None:
            try:
                return float(val1) < float(val2)
            except:
                pass
        text1 = self.text(col) or ""
        text2 = other.text(col) or ""
        return text1 < text2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("磁盘管家 Pro - 玄宇绘世工作室荣誉出品")
        self.resize(1200, 850)

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.system_scan_data = {}
        self.available_drives = FileEngine.get_available_drives()  # 获取所有盘符
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # === 侧边栏 ===
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(230)
        side_lyt = QVBoxLayout(self.sidebar)

        logo_lbl = QLabel("磁盘管家 PRO")
        logo_lbl.setStyleSheet("color: #00d1b2; font-size: 24px; font-weight: bold; margin: 20px 0;")
        side_lyt.addWidget(logo_lbl)

        menus = [
            ("⚡ 一键瘦身 (C盘)", 0),
            ("💬 社交/视频专项", 1),
            ("📊 高级大文件检索", 2),
            ("🔄 重复文件扫描", 3),
            ("ℹ️ 关于与免责声明", 4)
        ]
        for name, idx in menus:
            btn = QPushButton(name)
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda chk, i=idx: self.stack.setCurrentIndex(i))
            side_lyt.addWidget(btn)
        side_lyt.addStretch()
        layout.addWidget(self.sidebar)

        # === 主区域 ===
        content_lyt = QVBoxLayout()
        self.stack = QStackedWidget()

        self.stack.addWidget(self.init_system_page())
        self.stack.addWidget(self.init_app_page())
        self.stack.addWidget(self.init_large_page())
        self.stack.addWidget(self.init_duplicate_page())
        self.stack.addWidget(self.init_about_page())

        content_lyt.addWidget(self.stack)

        self.lbl_status = QLabel("系统准备就绪。")
        self.lbl_status.setStyleSheet("color: #666; padding: 10px; font-weight: bold;")
        content_lyt.addWidget(self.lbl_status)
        layout.addLayout(content_lyt)

    # ---------------- 核心UI与通用工厂方法 ----------------
    def init_system_page(self):
        page = QWidget()
        lyt = QVBoxLayout(page)
        header = QHBoxLayout()
        header.addWidget(QLabel("C盘核心清理：快速释放系统盘空间", font=QFont("Microsoft YaHei", 14, QFont.Bold)))

        self.btn_sys_scan = QPushButton("开始扫描")
        self.btn_sys_scan.setObjectName("actionBtn")
        self.btn_sys_scan.clicked.connect(lambda: self.start_scan("system"))

        self.btn_sys_clean = QPushButton("一键清理释放")
        self.btn_sys_clean.setObjectName("cleanBtn")
        self.btn_sys_clean.setEnabled(False)
        self.btn_sys_clean.clicked.connect(self.exec_system_clean)

        header.addWidget(self.btn_sys_scan)
        header.addWidget(self.btn_sys_clean)
        lyt.addLayout(header)

        self.sys_tree = QTreeWidget()
        self.sys_tree.setHeaderLabels(["清理项目", "可释放真实大小", "状态"])
        self.sys_tree.setSortingEnabled(True)
        self.sys_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

        for item in SYSTEM_CLEAN_CONFIG:
            tree_item = SafeSortItem([f"{item['icon']}  {item['name']}", "等待扫描", ""])
            tree_item.setData(0, Qt.UserRole, item['id'])
            tree_item.setCheckState(0, Qt.Checked if item['default'] else Qt.Unchecked)
            self.sys_tree.addTopLevelItem(tree_item)

        lyt.addWidget(self.sys_tree)
        return page

    def create_advanced_page(self, title, btn_scan_text, mode_name, columns, resize_col, show_threshold=False,
                             show_drives=False):
        """通用高级列表渲染工厂"""
        page = QWidget()
        lyt = QVBoxLayout(page)

        header_lyt = QVBoxLayout()
        title_lbl = QLabel(title, font=QFont("Microsoft YaHei", 12, QFont.Bold))
        header_lyt.addWidget(title_lbl)

        ctrl_lyt = QHBoxLayout()

        # 1. 动态盘符选择器（新增）
        if show_drives:
            ctrl_lyt.addWidget(QLabel("目标盘符:"))
            drive_combo = QComboBox()
            drive_combo.addItem("所有本地磁盘 (全盘)")
            for d in self.available_drives:
                drive_combo.addItem(f"仅扫描 {d}")
            drive_combo.setFixedWidth(160)
            ctrl_lyt.addWidget(drive_combo)
            setattr(self, f"{mode_name}_drive", drive_combo)
            ctrl_lyt.addSpacing(15)

        # 2. 动态阈值输入模块
        if show_threshold:
            ctrl_lyt.addWidget(QLabel("扫描阈值 (≥):"))
            spin_box = QSpinBox()
            spin_box.setRange(1, 999999)
            spin_box.setValue(100)
            spin_box.setFixedWidth(100)
            spin_box.setCursor(Qt.PointingHandCursor)
            ctrl_lyt.addWidget(spin_box)

            combo_box = QComboBox()
            combo_box.addItems(["MB", "GB"])
            combo_box.setFixedWidth(70)
            combo_box.setCursor(Qt.PointingHandCursor)
            ctrl_lyt.addWidget(combo_box)

            hint = QLabel("<font color='#888'>建议 ≥ 100MB</font>")
            ctrl_lyt.addWidget(hint)

            setattr(self, f"{mode_name}_spin", spin_box)
            setattr(self, f"{mode_name}_combo", combo_box)

        ctrl_lyt.addStretch()

        btn_scan = QPushButton(btn_scan_text)
        btn_scan.setObjectName("actionBtn")
        btn_scan.clicked.connect(lambda: self.start_scan(mode_name))

        btn_del = QPushButton("删除选中项")
        btn_del.setObjectName("delBtn")
        btn_del.clicked.connect(lambda: self.delete_selected_items(mode_name))

        ctrl_lyt.addWidget(btn_scan)
        ctrl_lyt.addWidget(btn_del)

        header_lyt.addLayout(ctrl_lyt)
        lyt.addLayout(header_lyt)

        tree = QTreeWidget()
        tree.setHeaderLabels(columns)
        tree.setSortingEnabled(True)
        # 【新增】：为第一列（文件名/智能分组）和第二列（大小）设定充足的初始宽度
        tree.setColumnWidth(0, 350)
        tree.setColumnWidth(1, 100)

        if len(columns) > 3:  # 如果有时间列（比如大文件/社交缓存），给时间列一点固定空间
            tree.setColumnWidth(2, 140)

        # 最后一列（路径）自适应伸展填满剩余空间
        tree.header().setSectionResizeMode(resize_col, QHeaderView.Stretch)

        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pos: self.show_context_menu(tree, pos))

        lyt.addWidget(tree)
        return page, tree

    def init_app_page(self):
        page, self.app_tree = self.create_advanced_page(
            "专项清理：安全粉碎微信/企微/视频软件的隐藏缓存", "扫描社交/视频缓存", "apps",
            ["所属应用分类 / 发现的文件", "物理占用空间", "修改时间", "文件完整路径"], 3, show_threshold=False,
            show_drives=False
        )
        return page

    def init_large_page(self):
        page, self.large_tree = self.create_advanced_page(
            "大文件检索：揪出硬盘中沉睡的系统庞然大物", "执行大文件扫描", "large",
            ["大文件名称", "物理占用空间", "创建/修改时间", "文件完整路径"], 3, show_threshold=True, show_drives=True
        )
        return page

    def init_duplicate_page(self):
        page, self.dup_tree = self.create_advanced_page(
            "重复文件：全盘比对特征码，杜绝同一视频/资料多处存放", "执行 MD5 查重", "duplicate",
            ["智能分组 / 重复文件名称", "物理占用空间", "发现的路径"], 2, show_threshold=True, show_drives=True
        )
        return page

    def init_about_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        page = QWidget()
        scroll.setWidget(page)
        main_lyt = QVBoxLayout(page)
        main_lyt.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_lyt.setContentsMargins(20, 40, 20, 40)

        container = QWidget()
        container.setFixedWidth(680)
        lyt = QVBoxLayout(container)
        lyt.setSpacing(25)

        # 1. Hero
        hero_widget = QWidget()
        hero_lyt = QVBoxLayout(hero_widget)
        hero_lyt.setAlignment(Qt.AlignCenter)
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            logo_lbl = QLabel()
            pixmap = QPixmap(logo_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pixmap)
            hero_lyt.addWidget(logo_lbl, alignment=Qt.AlignCenter)

        title = QLabel("磁盘管家 PRO")
        title.setStyleSheet("font-size: 32px; font-weight: 900; color: #0f172a; font-family: 'Microsoft YaHei';")
        hero_lyt.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = QLabel("由 玄宇绘世设计工作室 倾力打造")
        subtitle.setStyleSheet("font-size: 15px; color: #64748b; margin-top: 5px;")
        hero_lyt.addWidget(subtitle, alignment=Qt.AlignCenter)
        lyt.addWidget(hero_widget)

        # 2. Info Card
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_lyt = QVBoxLayout(info_card)
        info_lyt.setContentsMargins(25, 25, 25, 25)

        info_title = QLabel("ℹ️ 软件简介")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        info_lyt.addWidget(info_title)

        desc = QLabel(
            "一款专业级系统磁盘深度清理工具，专为解决 C 盘空间不足与冗余文件堆积设计。\n"
            "支持跨盘符大文件检索、MD5精准查重，及主流社交/媒体软件的安全专项缓存清理。\n"
            "纯本地运行，底层穿透虚假占用，告别弹窗广告，让您的工作电脑重获新生。"
        )
        desc.setStyleSheet("color: #475569; line-height: 1.6; font-size: 13px;")
        desc.setWordWrap(True)
        info_lyt.addWidget(desc)
        lyt.addWidget(info_card)

        # 3. Warn Card
        warn_card = QFrame()
        warn_card.setObjectName("warnCard")
        warn_lyt = QVBoxLayout(warn_card)
        warn_lyt.setContentsMargins(25, 25, 25, 25)

        warn_title = QLabel("⚠️ 重要操作警告与免责声明")
        warn_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #b91c1c; margin-bottom: 10px;")
        warn_lyt.addWidget(warn_title)

        warn_text = QLabel(
            "1. 本软件执行的所有删除指令均为<b>「彻底物理删除」</b>，文件不会进入系统回收站，不可恢复。<br><br>"
            "2. 清理前请务必仔细核对勾选列表，特别是<b>“全盘大文件”</b>与<b>“重复文件”</b>模块，避免误删您的私人照片、工作资料或模型资产。<br><br>"
            "3. 本工具为免费开源项目，开发者（玄宇绘世设计工作室）已尽力确保算法安全并规避了核心数据库，但<b>不对任何因用户人为误操作、意外系统断电等情况造成的数据丢失承担任何法律及赔偿责任</b>。<br><br>"
            "<font color='#991b1b'><b>继续使用本软件，即代表您已知晓、理解并自愿同意上述所有免责条款！</b></font>"
        )
        warn_text.setStyleSheet("color: #7f1d1d; line-height: 1.6; font-size: 13px;")
        warn_text.setWordWrap(True)
        warn_text.setTextFormat(Qt.RichText)
        warn_lyt.addWidget(warn_text)
        lyt.addWidget(warn_card)

        # 4. Footer
        footer = QLabel("Copyright © 2026 玄宇绘世设计工作室|XY·D Studio. All Rights Reserved.")
        footer.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 20px;")
        lyt.addWidget(footer, alignment=Qt.AlignCenter)

        btn_lyt = QHBoxLayout()
        btn_website = QPushButton("🌐 访问 玄宇绘世设计工作室 官网")
        btn_website.setCursor(Qt.PointingHandCursor)  # 鼠标放上去变小手
        btn_website.setFixedWidth(280)
        btn_website.setFixedHeight(45)

        # 为这个专属按钮单独写行内高颜值样式
        btn_website.setStyleSheet("""
                    QPushButton {
                        background-color: #0ea5e9;
                        color: white;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #0284c7;
                    }
                    QPushButton:pressed {
                        background-color: #0369a1;
                    }
                """)


        target_url = "https://www.xy-d.top"
        btn_website.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(target_url)))

        btn_lyt.addWidget(btn_website, alignment=Qt.AlignCenter)
        lyt.addLayout(btn_lyt)

        # 增加一点底部留白
        lyt.addSpacing(10)

        main_lyt.addWidget(container)
        return scroll

    # ---------------- 业务逻辑分发处理 ----------------
    def get_target_drives(self, mode):
        """解析下拉菜单，返回用户要扫描的具体盘符列表"""
        if not hasattr(self, f"{mode}_drive"): return self.available_drives
        combo = getattr(self, f"{mode}_drive")
        idx = combo.currentIndex()
        if idx == 0:
            return self.available_drives  # 选了全盘
        else:
            return [self.available_drives[idx - 1]]  # 选了具体的如 D:\

    def get_threshold_bytes(self, mode):
        if not hasattr(self, f"{mode}_spin"): return 100 * 1024 * 1024
        val = getattr(self, f"{mode}_spin").value()
        unit = getattr(self, f"{mode}_combo").currentText()
        return val * 1024 * 1024 if unit == "MB" else val * 1024 * 1024 * 1024

    def show_context_menu(self, tree, pos):
        item = tree.itemAt(pos)
        if not item: return
        path = item.text(tree.columnCount() - 1)
        if not path or not os.path.exists(path): return
        menu = QMenu()
        action = menu.addAction("📂 在文件资源管理器中定位所在目录")
        action.triggered.connect(lambda: os.startfile(os.path.dirname(path)))
        menu.exec(QCursor.pos())

    def start_scan(self, mode):
        # 提取参数
        threshold = self.get_threshold_bytes(mode) if mode in ["large", "duplicate"] else 0
        target_drives = self.get_target_drives(mode) if mode in ["large", "duplicate"] else []

        if mode == "duplicate" and threshold < 50 * 1024 * 1024:
            reply = QMessageBox.warning(
                self, "严重耗时警告",
                "您设置的重复文件扫描阈值小于 50MB。\n全盘计算海量小文件的特征码将极度消耗系统性能，可能耗时数十分钟，并造成机械硬盘高度读写磨损。\n\n是否坚持继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No: return

        self.btn_sys_clean.setEnabled(False)
        self.lbl_status.setText("后台扫描引擎已启动，正在穿透分析深层目录...")

        if mode == "system":
            self.system_scan_data.clear()
            for i in range(self.sys_tree.topLevelItemCount()):
                self.sys_tree.topLevelItem(i).setText(1, "扫描中...")
                self.sys_tree.topLevelItem(i).setText(2, "")
        elif mode == "apps":
            self.app_tree.clear()
        elif mode == "large":
            self.large_tree.clear()
        elif mode == "duplicate":
            self.dup_tree.clear()

        self.worker = ScanWorker(mode, threshold_bytes=threshold, target_drives=target_drives)
        self.worker.progress_msg.connect(lambda msg: self.lbl_status.setText(msg))
        self.worker.result_data.connect(self.on_scan_result)
        self.worker.finished_scan.connect(lambda: self.on_scan_finished(mode))
        self.worker.start()

    def on_scan_result(self, data):
        if data["type"] == "system":
            self.system_scan_data[data["id"]] = data["size"]
            for i in range(self.sys_tree.topLevelItemCount()):
                item = self.sys_tree.topLevelItem(i)
                if item.data(0, Qt.UserRole) == data["id"]:
                    item.setText(1, FileEngine.format_size(data["size"]))
                    item.setData(1, Qt.UserRole, data["size"])
        elif data["type"] == "app":
            parent = SafeSortItem([f"📂 [{data['category']}] {data['app_name']} - 发现可清理缓存", "", "", ""])
            parent.setExpanded(True)
            self.app_tree.addTopLevelItem(parent)
            for f in data["files"]:
                mtime_str = datetime.fromtimestamp(f["mtime"]).strftime('%Y-%m-%d %H:%M')
                child = SafeSortItem([f["name"], FileEngine.format_size(f["size"]), mtime_str, f["path"]])
                child.setData(1, Qt.UserRole, f["size"])
                child.setCheckState(0, Qt.Unchecked)
                parent.addChild(child)
        elif data["type"] == "large":
            mtime_str = datetime.fromtimestamp(data["mtime"]).strftime('%Y-%m-%d %H:%M')
            item = SafeSortItem(
                [os.path.basename(data["path"]), FileEngine.format_size(data["size"]), mtime_str, data["path"]])
            item.setData(1, Qt.UserRole, data["size"])
            item.setCheckState(0, Qt.Unchecked)
            self.large_tree.addTopLevelItem(item)
        elif data["type"] == "duplicate":
            size_str = FileEngine.format_size(data["size"])
            parent = SafeSortItem(
                [f"📑 此文件在硬盘上有 {len(data['paths'])} 个相同的副本", size_str, "请展开勾选需要粉碎的重复项"])
            parent.setData(1, Qt.UserRole, data["size"])
            parent.setExpanded(True)
            self.dup_tree.addTopLevelItem(parent)
            for p in data["paths"]:
                child = SafeSortItem([os.path.basename(p), size_str, p])
                child.setCheckState(0, Qt.Unchecked)
                parent.addChild(child)

    def on_scan_finished(self, mode):
        if mode == "system":
            total = sum(self.system_scan_data.values())
            self.lbl_status.setText(f"扫描完毕！系统盘 C盘 共发现 {FileEngine.format_size(total)} 垃圾文件。")
            self.btn_sys_clean.setEnabled(True)
        else:
            self.lbl_status.setText(
                "深度扫描已完成！请在上方列表中打钩选中需要删除的文件，点击【删除选中项】，或通过右键定位目录。")

    # ================== 【核心修复】深度删除与层级解算 ==================
    def exec_system_clean(self):
        self.btn_sys_clean.setEnabled(False)
        freed_bytes = 0
        for i in range(self.sys_tree.topLevelItemCount()):
            item = self.sys_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                target_id = item.data(0, Qt.UserRole)
                paths = next(c['paths'] for c in SYSTEM_CLEAN_CONFIG if c['id'] == target_id)
                for p in paths:
                    if not os.path.exists(p): continue
                    for root, _, files in os.walk(p):
                        for f in files:
                            try:
                                fp = os.path.join(root, f)
                                sz = FileEngine.get_physical_size(fp)  # 使用真实物理大小累加释放量
                                os.remove(fp)
                                freed_bytes += sz
                            except:
                                pass
                item.setText(1, "0 B")
                item.setData(1, Qt.UserRole, 0)
                item.setText(2, "✅ 已清理释放")
                item.setCheckState(0, Qt.Unchecked)

        self.lbl_status.setText(f"C盘清理成功！为您腾出 {FileEngine.format_size(freed_bytes)} 的物理空间。")
        QMessageBox.information(self, "操作完成", f"恭喜！C盘成功释放 {FileEngine.format_size(freed_bytes)} 物理容量。")

    def delete_selected_items(self, mode):
        """修复了父子结构下的删除逻辑，确保准确提取最后一列的真实路径"""
        reply = QMessageBox.warning(self, "危险操作确认",
                                    "【高危提示】选中的文件将被彻底物理粉碎，不进入回收站。\n\n您确定要永久删除所有打钩项吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        tree = getattr(self, f"{mode}_tree" if mode != "apps" else "app_tree")
        freed = 0
        items_to_remove = []

        # 1. 精准提取所有被打钩的节点
        for i in range(tree.topLevelItemCount()):
            top_item = tree.topLevelItem(i)
            # 模式 A: 平级结构 (全盘大文件)
            if mode == "large":
                if top_item.checkState(0) == Qt.Checked:
                    items_to_remove.append(top_item)
            # 模式 B: 父子树状结构 (社交缓存、重复文件)
            else:
                for j in range(top_item.childCount()):
                    child = top_item.child(j)
                    if child.checkState(0) == Qt.Checked:
                        items_to_remove.append(child)

        if not items_to_remove:
            QMessageBox.information(self, "提示", "您还没有勾选任何文件！")
            return

        # 2. 执行物理删除与 UI 剥离
        failed_count = 0
        for item in items_to_remove:
            path = item.text(tree.columnCount() - 1)  # 严格读取最后一列的 Path 字符串
            if os.path.exists(path):
                try:
                    sz = FileEngine.get_physical_size(path)
                    os.remove(path)
                    freed += sz
                    (item.parent() or tree.invisibleRootItem()).removeChild(item)
                except Exception as e:
                    failed_count += 1

        # 3. 反馈结果
        msg = f"成功粉碎选中文件！共释放 {FileEngine.format_size(freed)} 的真实磁盘空间。"
        if failed_count > 0: msg += f"\n注：有 {failed_count} 个文件因被系统或其它程序占用而跳过。"

        self.lbl_status.setText("执行完毕。")
        QMessageBox.information(self, "清理报告", msg)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f9fa; }
            #sidebar { background-color: #1e293b; border: none; }
            #sidebar QPushButton { 
                background: transparent; color: #94a3b8; border: none; 
                text-align: left; padding-left: 20px; font-size: 14px; font-weight: bold;
            }
            #sidebar QPushButton:hover { background: #334155; color: white; border-left: 4px solid #38bdf8; }
            #sidebar QPushButton:focus { background: #0f172a; color: #38bdf8; border-left: 4px solid #38bdf8; }

            #actionBtn { background-color: #3b82f6; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; }
            #actionBtn:hover { background-color: #2563eb; }

            #cleanBtn { background-color: #10b981; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; }
            #cleanBtn:hover { background-color: #059669; }
            #cleanBtn:disabled { background-color: #cbd5e1; color: #64748b; }

            #delBtn { background-color: #ef4444; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; }
            #delBtn:hover { background-color: #dc2626; }

            /* 列表树样式 */
            QTreeWidget { border: 1px solid #e2e8f0; background: #ffffff; font-size: 13px; color: #334155; outline: 0; }
            QHeaderView::section { background-color: #f1f5f9; padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e293b; }
            QTreeWidget::item:selected { background-color: #e0f2fe; color: #0369a1; }
            QTreeWidget::item { padding: 5px 0; border-bottom: 1px solid #f8fafc; }

            /* 卡片样式 */
            #infoCard { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }
            #warnCard { background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 9))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())