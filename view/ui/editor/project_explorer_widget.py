"""Project Explorer Widget - File tree navigation with right-click context menu,
file creation, renaming, deletion, and folder opening.
"""
import os
import subprocess
from typing import Union, overload
from PyQt6.QtCore import Qt, QModelIndex, QDir, QFileInfo, pyqtSignal
from PyQt6.QtGui import QIcon, QFileSystemModel, QAbstractFileIconProvider
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QPushButton,
    QLabel, QInputDialog, QMessageBox, QMenu, QFileDialog, QHeaderView
)

from view.ui.icons import create_vector_icon


class MonochromeFileIconProvider(QAbstractFileIconProvider):
    """Provides sleek 2D monochrome icons for folders and files, eliminating yellow icons."""

    @overload
    def icon(self, a0: QAbstractFileIconProvider.IconType) -> QIcon: ...

    @overload
    def icon(self, a0: QFileInfo) -> QIcon: ...

    def icon(self, a0: Union[QAbstractFileIconProvider.IconType, QFileInfo]) -> QIcon:
        try:
            if isinstance(a0, QFileInfo):
                if a0.isDir():
                    return create_vector_icon("folder", "#94A3B8", 16)
                return create_vector_icon("file", "#64748B", 16)
            elif isinstance(a0, QAbstractFileIconProvider.IconType):
                if a0 in (QAbstractFileIconProvider.IconType.Folder, QAbstractFileIconProvider.IconType.Drive):
                    return create_vector_icon("folder", "#94A3B8", 16)
                return create_vector_icon("file", "#64748B", 16)
        except Exception:
            pass
        return super().icon(a0)


class ProjectExplorerWidget(QWidget):
    """File Tree Explorer for the current coding workspace."""

    fileSelected = pyqtSignal(str)
    folderOpened = pyqtSignal(str)

    def __init__(self, parent=None, root_path: str = ""):
        super().__init__(parent)
        self.root_path = root_path or os.getcwd()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with Workspace Title & Quick Action Buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.title_lbl = QLabel("DỰ ÁN")
        self.title_lbl.setStyleSheet("color: #94A3B8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        header_layout.addWidget(self.title_lbl, stretch=1)

        # Quick action buttons (clean 2D monochrome, no emojis)
        self.btn_open_folder = QPushButton("Mở")
        self.btn_open_folder.setToolTip("Mở thư mục khác...")
        self.btn_open_folder.setFixedHeight(24)
        self.btn_open_folder.clicked.connect(self._choose_folder)

        self.btn_new_file = QPushButton("+F")
        self.btn_new_file.setToolTip("Tạo file mới...")
        self.btn_new_file.setFixedSize(26, 24)
        self.btn_new_file.clicked.connect(self._create_new_file)

        self.btn_new_folder = QPushButton("+D")
        self.btn_new_folder.setToolTip("Tạo thư mục mới...")
        self.btn_new_folder.setFixedSize(26, 24)
        self.btn_new_folder.clicked.connect(self._create_new_folder)

        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setToolTip("Làm mới danh sách")
        self.btn_refresh.setFixedSize(24, 24)
        self.btn_refresh.clicked.connect(self.refresh)

        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                color: #CBD5E1;
                font-size: 11px;
                font-weight: 600;
                padding: 0 4px;
            }
            QPushButton:hover {
                background: rgba(0, 255, 170, 0.12);
                border-color: #00FFAA;
                color: #00FFAA;
            }
        """
        for btn in (self.btn_open_folder, self.btn_new_file, self.btn_new_folder, self.btn_refresh):
            btn.setStyleSheet(btn_style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            header_layout.addWidget(btn)

        layout.addLayout(header_layout)

        # File System Model with Monochrome 2D Icons
        self.model = QFileSystemModel()
        self.icon_provider = MonochromeFileIconProvider()
        self.model.setIconProvider(self.icon_provider)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self.model.setRootPath(self.root_path)

        # Tree View
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        self.tree_view.setHeaderHidden(True)

        # Hide extra columns (Size, Type, Date Modified)
        for col in range(1, 4):
            self.tree_view.hideColumn(col)

        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(16)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)

        # PopView Transparent Glass styling
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: rgba(6, 10, 18, 0.45);
                color: #CBD5E1;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }
            QTreeView::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QTreeView::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #00FFAA;
            }
            QTreeView::item:selected {
                background-color: rgba(0, 255, 170, 0.12);
                border: 1px solid rgba(0, 255, 170, 0.35);
                color: #FFFFFF;
                font-weight: 600;
            }
        """)

        layout.addWidget(self.tree_view, stretch=1)
        self.set_workspace(self.root_path)

    def set_workspace(self, folder_path: str):
        if not os.path.exists(folder_path):
            return
        self.root_path = os.path.abspath(folder_path)
        self.model.setRootPath(self.root_path)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        folder_name = os.path.basename(self.root_path) or self.root_path
        self.title_lbl.setText("DỰ ÁN")
        self.title_lbl.setToolTip(f"Thư mục làm việc: {self.root_path}")
        self.folderOpened.emit(self.root_path)

    open_directory = set_workspace
    open_folder = set_workspace

    def refresh(self):
        self.model.setRootPath("")
        self.model.setRootPath(self.root_path)
        self.tree_view.setRootIndex(self.model.index(self.root_path))

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án", self.root_path)
        if folder:
            self.set_workspace(folder)

    def _on_item_double_clicked(self, index: QModelIndex):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.fileSelected.emit(file_path)

    def _get_target_dir_for_creation(self) -> str:
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            sel_path = self.model.filePath(indexes[0])
            if os.path.isdir(sel_path):
                return sel_path
            return os.path.dirname(sel_path)
        return self.root_path

    def _create_new_file(self):
        target_dir = self._get_target_dir_for_creation()
        name, ok = QInputDialog.getText(self, "Tạo File Mới", "Tên file (ví dụ: main.py, script.js):")
        if ok and name.strip():
            full_path = os.path.join(target_dir, name.strip())
            if os.path.exists(full_path):
                QMessageBox.warning(self, "Lỗi", "File đã tồn tại!")
                return
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.fileSelected.emit(full_path)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi tạo file", str(e))

    def _create_new_folder(self):
        target_dir = self._get_target_dir_for_creation()
        name, ok = QInputDialog.getText(self, "Tạo Thư Mục Mới", "Tên thư mục:")
        if ok and name.strip():
            full_path = os.path.join(target_dir, name.strip())
            if os.path.exists(full_path):
                QMessageBox.warning(self, "Lỗi", "Thư mục đã tồn tại!")
                return
            try:
                os.makedirs(full_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi tạo thư mục", str(e))

    def _show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #0D111A;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
                color: #E2E8F0;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(0, 255, 170, 0.2);
                color: #00FFAA;
            }
        """)

        file_path = self.model.filePath(index) if index.isValid() else self.root_path
        is_file = os.path.isfile(file_path)

        if is_file:
            menu.addAction("Mở file", lambda: self.fileSelected.emit(file_path))
            menu.addSeparator()

        menu.addAction("Tạo file mới...", self._create_new_file)
        menu.addAction("Tạo thư mục mới...", self._create_new_folder)
        menu.addSeparator()

        if index.isValid():
            menu.addAction("Đổi tên", lambda: self._rename_item(file_path))
            menu.addAction("Xóa", lambda: self._delete_item(file_path))
            menu.addSeparator()

        menu.addAction("Sao chép đường dẫn", lambda: self._copy_path(file_path))
        menu.addAction("Mở trong Explorer", lambda: self._reveal_in_explorer(file_path))

        vp = self.tree_view.viewport()
        global_pos = vp.mapToGlobal(pos) if vp is not None else self.tree_view.mapToGlobal(pos)
        menu.exec(global_pos)

    def _rename_item(self, old_path: str):
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Đổi tên", "Tên mới:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            parent_dir = os.path.dirname(old_path)
            new_path = os.path.join(parent_dir, new_name.strip())
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi đổi tên", str(e))

    def _delete_item(self, path: str):
        name = os.path.basename(path)
        res = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa '{name}' vĩnh viễn không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi xóa", str(e))

    def _copy_path(self, path: str):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(path)

    def _reveal_in_explorer(self, path: str):
        try:
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
            else:
                subprocess.Popen(f'explorer "{os.path.normpath(path)}"')
        except Exception as e:
            QMessageBox.warning(self, "Lỗi mở Explorer", str(e))

