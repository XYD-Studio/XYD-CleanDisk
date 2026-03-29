import sys
import os

def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境与 PyInstaller 打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境的当前目录
    return os.path.join(os.path.abspath("."), relative_path)

from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTreeWidget,
                               QTreeWidgetItem, QStackedWidget, QHeaderView, QFrame,
                               QMessageBox, QMenu, QSpinBox, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QCursor, QPixmap

from config import SYSTEM_CLEAN_CONFIG
from engine import FileEngine, ScanWorker


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
        self.setWindowTitle("磁盘管家 Pro - 玄宇绘世设计工作室")
        self.resize(1200, 850)

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.system_scan_data = {}
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 侧边栏
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
            ("📊 全盘大文件", 2),
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

        # 主区域
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

    # ---------------- 页面初始化 ----------------
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
        self.sys_tree.setHeaderLabels(["清理项目", "可释放大小", "状态"])
        self.sys_tree.setSortingEnabled(True)
        self.sys_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

        for item in SYSTEM_CLEAN_CONFIG:
            tree_item = SafeSortItem([f"{item['icon']}  {item['name']}", "等待扫描", ""])
            tree_item.setData(0, Qt.UserRole, item['id'])
            tree_item.setCheckState(0, Qt.Checked if item['default'] else Qt.Unchecked)
            self.sys_tree.addTopLevelItem(tree_item)

        lyt.addWidget(self.sys_tree)
        return page

    def create_advanced_page(self, title, btn_scan_text, mode_name, columns, resize_col, show_threshold=False):
        page = QWidget()
        lyt = QVBoxLayout(page)

        # 头部标题与控制区
        header_lyt = QVBoxLayout()
        title_lbl = QLabel(title, font=QFont("Microsoft YaHei", 12, QFont.Bold))
        header_lyt.addWidget(title_lbl)

        ctrl_lyt = QHBoxLayout()

        # 动态阈值输入模块
        if show_threshold:
            ctrl_lyt.addWidget(QLabel("扫描阈值 (≥):"))

            spin_box = QSpinBox()
            spin_box.setRange(1, 999999)
            spin_box.setValue(100)
            spin_box.setFixedWidth(100)
            spin_box.setCursor(Qt.PointingHandCursor)  # 鼠标放上去变手型
            ctrl_lyt.addWidget(spin_box)

            combo_box = QComboBox()
            combo_box.addItems(["MB", "GB"])
            combo_box.setFixedWidth(70)
            spin_box.setCursor(Qt.PointingHandCursor)  # 鼠标放上去变手型
            ctrl_lyt.addWidget(combo_box)

            hint = QLabel("<font color='#888'>建议 ≥ 100MB，保障检索效率</font>")
            ctrl_lyt.addWidget(hint)

            # 将控件存入实例变量以便读取
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
        tree.header().setSectionResizeMode(resize_col, QHeaderView.Stretch)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pos: self.show_context_menu(tree, pos))

        lyt.addWidget(tree)
        return page, tree

    def init_app_page(self):
        page, self.app_tree = self.create_advanced_page(
            "专项清理：勾选并删除不需要的媒体/社交缓存", "开始扫描缓存", "apps",
            ["应用分类 / 文件名", "文件大小", "修改时间", "完整路径"], 3, show_threshold=False
        )
        return page

    def init_large_page(self):
        page, self.large_tree = self.create_advanced_page(
            "全盘大文件：找出并勾选隐藏的超大文件", "全盘扫描大文件", "large",
            ["大文件名称", "占用大小", "修改时间", "文件路径"], 3, show_threshold=True
        )
        return page

    def init_duplicate_page(self):
        page, self.dup_tree = self.create_advanced_page(
            "重复文件：全盘比对特征码找出冗余副本", "全盘查重", "duplicate",
            ["文件名 / 重复组", "文件大小", "发现的路径"], 2, show_threshold=True
        )
        return page

    def init_about_page(self):
        # 使用 QScrollArea 防止小窗口下内容被裁切
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        page = QWidget()
        scroll.setWidget(page)

        # 主布局：居中对齐
        main_lyt = QVBoxLayout(page)
        main_lyt.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_lyt.setContentsMargins(20, 40, 20, 40)

        # 创建一个限制最大宽度的容器（卡片设计的精髓，防止超宽屏变形）
        container = QWidget()
        container.setFixedWidth(680)
        lyt = QVBoxLayout(container)
        lyt.setSpacing(25)  # 模块间距

        # ==========================================
        # 1. 顶部 Hero Section (Logo 与 标题)
        # ==========================================
        hero_widget = QWidget()
        hero_lyt = QVBoxLayout(hero_widget)
        hero_lyt.setAlignment(Qt.AlignCenter)
        hero_lyt.setSpacing(10)

        # Logo
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            logo_lbl = QLabel()
            pixmap = QPixmap(logo_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pixmap)
            hero_lyt.addWidget(logo_lbl, alignment=Qt.AlignCenter)

        # 软件名称
        title = QLabel("磁盘管家 PRO")
        title.setStyleSheet("font-size: 32px; font-weight: 900; color: #0f172a; font-family: 'Microsoft YaHei';")
        hero_lyt.addWidget(title, alignment=Qt.AlignCenter)

        # 版本号 Badge
        version_lbl = QLabel("Version 1.0.0 (Release)")
        version_lbl.setStyleSheet("""
            background-color: #e0f2fe; color: #0284c7; font-weight: bold; 
            padding: 4px 12px; border-radius: 12px; font-size: 12px;
        """)
        hero_lyt.addWidget(version_lbl, alignment=Qt.AlignCenter)

        # 工作室署名
        subtitle = QLabel("由 玄宇绘世设计工作室 倾力打造")
        subtitle.setStyleSheet("font-size: 15px; color: #64748b; margin-top: 5px;")
        hero_lyt.addWidget(subtitle, alignment=Qt.AlignCenter)

        lyt.addWidget(hero_widget)

        # ==========================================
        # 2. 软件信息卡片 (白色质感)
        # ==========================================
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_lyt = QVBoxLayout(info_card)
        info_lyt.setContentsMargins(25, 25, 25, 25)
        info_lyt.setSpacing(15)

        info_title = QLabel("ℹ️ 软件简介")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        info_lyt.addWidget(info_title)

        desc = QLabel(
            "一款专业级系统磁盘深度清理工具，专为解决C盘空间不足与电脑冗余文件堆积设计。\n"
            "支持跨盘符大文件检索、MD5精准查重，及主流社交/媒体软件的专项缓存清理。\n"
            "纯本地运行，彻底告别弹窗与流氓后台，显著提升系统运行效率。"
        )
        desc.setStyleSheet("color: #475569; line-height: 1.6; font-size: 13px;")
        desc.setWordWrap(True)
        info_lyt.addWidget(desc)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("border-top: 1px solid #e2e8f0; margin: 10px 0;")
        info_lyt.addWidget(line)

        # 链接区域
        links_lbl = QLabel(
            "<a href='https://www.home.xy-d.top/' style='color: #0284c7; text-decoration: none;'>🌐 访问官网</a>"
            "&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;"
            "<a href='https://github.com/XYD-Studio/' style='color: #0284c7; text-decoration: none;'>⭐ GitHub 开源主页</a>"
            "&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;"
            "<a href='mailto:xydstudio@xy-d.top' style='color: #0284c7; text-decoration: none;'>✉️ 商业合作与反馈</a>"
        )
        links_lbl.setOpenExternalLinks(True)
        links_lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        info_lyt.addWidget(links_lbl, alignment=Qt.AlignCenter)

        lyt.addWidget(info_card)

        # ==========================================
        # 3. 警告与免责声明卡片 (红色警示质感)
        # ==========================================
        warn_card = QFrame()
        warn_card.setObjectName("warnCard")
        warn_lyt = QVBoxLayout(warn_card)
        warn_lyt.setContentsMargins(25, 25, 25, 25)
        warn_lyt.setSpacing(15)

        warn_title = QLabel("⚠️ 重要操作警告与免责声明")
        warn_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #b91c1c;")
        warn_lyt.addWidget(warn_title)

        warn_text = QLabel(
            "1. 本软件执行的所有删除指令均为<b>「彻底物理删除」</b>，文件不会进入系统回收站，不可恢复。<br><br>"
            "2. 清理前请务必仔细核对勾选列表，特别是<b>“全盘大文件”</b>与<b>“重复文件”</b>模块，避免误删重要的个人资料、工程文件或系统运行依赖项。<br><br>"
            "3. 本工具为免费开源项目，开发者（玄宇绘世设计工作室）已尽力确保算法安全并加入防呆机制，但<b>不对任何因用户误操作、未知的系统环境冲突或软件 Bug 导致的数据丢失、硬盘损坏或系统崩溃承担任何法律及赔偿责任</b>。<br><br>"
            "<font color='#991b1b'><b>继续使用本软件，即代表您已知晓、理解并自愿同意上述所有免责条款！</b></font>"
        )
        warn_text.setStyleSheet("color: #7f1d1d; line-height: 1.6; font-size: 13px;")
        warn_text.setWordWrap(True)
        warn_text.setTextFormat(Qt.RichText)
        warn_lyt.addWidget(warn_text)

        lyt.addWidget(warn_card)

        # ==========================================
        # 4. 底部版权信息
        # ==========================================
        footer = QLabel("Copyright © 2026 玄宇绘世设计工作室|XY·D Studio. All Rights Reserved.")
        footer.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 20px;")
        lyt.addWidget(footer, alignment=Qt.AlignCenter)

        main_lyt.addWidget(container)
        return scroll

    # ---------------- 核心交互逻辑 ----------------
    def get_threshold_bytes(self, mode):
        """获取并计算阈值大小（字节）"""
        if not hasattr(self, f"{mode}_spin"): return 100 * 1024 * 1024

        val = getattr(self, f"{mode}_spin").value()
        unit = getattr(self, f"{mode}_combo").currentText()
        return val * 1024 * 1024 if unit == "MB" else val * 1024 * 1024 * 1024

    def show_context_menu(self, tree, pos):
        item = tree.itemAt(pos)
        if not item: return

        path = None
        for col in range(tree.columnCount()):
            text = item.text(col)
            if text and ":\\" in text and os.path.exists(text):
                path = text
                break

        if not path: return

        menu = QMenu()
        action = menu.addAction("📂 打开文件所在目录")
        action.triggered.connect(lambda: os.startfile(os.path.dirname(path)))
        menu.exec(QCursor.pos())

    def start_scan(self, mode):
        # --- 校验重复文件的极小阈值 ---
        threshold = 0
        if mode in ["large", "duplicate"]:
            threshold = self.get_threshold_bytes(mode)
            if mode == "duplicate" and threshold < 50 * 1024 * 1024:
                reply = QMessageBox.warning(
                    self, "严重耗时警告",
                    "您设置的重复文件扫描阈值过小（小于 50MB）。\n\n"
                    "全盘计算海量小文件的 MD5 特征码极度消耗系统性能，可能耗时数十分钟，并造成机械硬盘高度读写磨损。\n\n是否坚持继续？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No: return

        self.btn_sys_clean.setEnabled(False)
        self.lbl_status.setText("正在执行高性能扫描，请稍候...")

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

        # 传入动态计算的阈值
        self.worker = ScanWorker(mode, threshold_bytes=threshold)
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
            parent = SafeSortItem([f"📂 [{data['category']}] {data['app_name']}", "", "", ""])
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
            parent = SafeSortItem([f"📑 发现重复项 ({len(data['paths'])}个副本)", size_str, "请展开勾选需要删除的副本"])
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
            self.lbl_status.setText(f"扫描完毕！C盘共发现 {FileEngine.format_size(total)} 可释放空间。")
            self.btn_sys_clean.setEnabled(True)
        else:
            self.lbl_status.setText("高级扫描完成！请勾选需要删除的文件，点击右上角【删除选中项】，或右键打开目录。")

    # ================== 清理执行逻辑 ==================
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
                    for root, dirs, files in os.walk(p):
                        for f in files:
                            try:
                                fp = os.path.join(root, f)
                                sz = os.path.getsize(fp)
                                os.remove(fp)
                                freed_bytes += sz
                            except:
                                pass
                item.setText(1, "0 B")
                item.setData(1, Qt.UserRole, 0)
                item.setText(2, "✅ 已清理")
                item.setCheckState(0, Qt.Unchecked)

        self.lbl_status.setText(f"C盘瘦身成功！为您腾出 {FileEngine.format_size(freed_bytes)} 空间。")
        QMessageBox.information(self, "清理完成", f"C盘成功释放 {FileEngine.format_size(freed_bytes)}。")

    def delete_selected_items(self, mode):
        reply = QMessageBox.warning(self, "严重警告", "文件删除后不可恢复（不进回收站）！\n确定要删除选中的所有文件吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        tree = getattr(self, f"{mode}_tree" if mode != "apps" else "app_tree")
        freed = 0
        items_to_remove = []

        for i in range(tree.topLevelItemCount()):
            top_item = tree.topLevelItem(i)
            if mode == "large":
                if top_item.checkState(0) == Qt.Checked: items_to_remove.append(top_item)
            else:
                for j in range(top_item.childCount()):
                    child = top_item.child(j)
                    if child.checkState(0) == Qt.Checked: items_to_remove.append(child)

        for item in items_to_remove:
            path = item.text(tree.columnCount() - 1)
            if os.path.exists(path):
                try:
                    sz = os.path.getsize(path)
                    os.remove(path)
                    freed += sz
                    (item.parent() or tree.invisibleRootItem()).removeChild(item)
                except Exception as e:
                    self.lbl_status.setText(f"跳过被占用文件: {path}")

        QMessageBox.information(self, "删除成功", f"成功删除选中文件，共腾出 {FileEngine.format_size(freed)}。")

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

            /* =======================================
               修复与美化：下拉框和数值调节框
               ======================================= */
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: white;
                padding-left: 10px;
                min-height: 26px;
                color: #334155;
            }
            QComboBox:hover { border: 1px solid #94a3b8; }
            QComboBox:focus { border: 1px solid #38bdf8; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #cbd5e1;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background: #f8fafc;
            }

            QSpinBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: white;
                /* 只给左侧 padding，保护右侧按钮热区不被遮挡 */
                padding-left: 10px; 
                min-height: 26px;
                color: #334155;
            }
            QSpinBox:hover { border: 1px solid #94a3b8; }
            QSpinBox:focus { border: 1px solid #38bdf8; }
            /* 美化上下调节按钮 */
            QSpinBox::up-button, QSpinBox::down-button {
                width: 24px;
                background: #f8fafc;
                border-left: 1px solid #cbd5e1;
            }
            QSpinBox::up-button {
                border-bottom: 1px solid #cbd5e1;
                border-top-right-radius: 4px;
            }
            QSpinBox::down-button {
                border-bottom-right-radius: 4px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #e2e8f0; }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed { background: #cbd5e1; }

            /* =======================================
               列表树样式
               ======================================= */
            QTreeWidget { 
                border: 1px solid #e2e8f0; background: #ffffff; font-size: 13px; color: #334155; outline: 0;
            }
            QHeaderView::section { 
                background-color: #f1f5f9; padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e293b;
            }
            QTreeWidget::item:selected { background-color: #e0f2fe; color: #0369a1; }
            QTreeWidget::item { padding: 5px 0; border-bottom: 1px solid #f8fafc; }
                        /* =======================================
               关于页面：卡片式 UI 样式
               ======================================= */
            #infoCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            #warnCard {
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 12px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())