"""
POP Input Bar Model - Quản lý dữ liệu và logic nghiệp vụ cho Input Bar (Model Layer).
Tuân thủ nghiêm ngặt mô hình MVC:
- Quản lý danh sách tệp đính kèm và tổng hợp nội dung văn bản / prompt.
- Quét và phát hiện các mô hình local GGUF từ thư mục cấu hình.
"""

import os
from typing import List, Tuple, Optional
from view.ui.settings import load_user_settings
from utils.document_reader import read_document_file


class InputBarModel:
    """Model quản lý trạng thái tệp đính kèm và danh sách mô hình AI cục bộ."""

    def __init__(self):
        self._attached_files: List[str] = []
        self._selected_model: str = "Auto"

    # ----------------------------------------------------
    # QUẢN LÝ TỆP ĐÍNH KÈM (ATTACHMENTS)
    # ----------------------------------------------------

    def get_attached_files(self) -> List[str]:
        """Trả về bản sao danh sách đường dẫn tệp đính kèm."""
        return list(self._attached_files)

    def add_attached_files(self, file_paths: List[str]) -> bool:
        """Thêm các tệp đính kèm mới nếu tệp tồn tại và chưa có trong danh sách.
        Trả về True nếu có ít nhất một tệp mới được thêm."""
        new_added = False
        for path in file_paths:
            if not os.path.exists(path) or path in self._attached_files:
                continue
            self._attached_files.append(path)
            new_added = True
        return new_added

    def remove_attached_file(self, file_path: str) -> bool:
        """Xóa một tệp đính kèm khỏi danh sách."""
        if file_path in self._attached_files:
            self._attached_files.remove(file_path)
            return True
        return False

    def clear_attached_files(self) -> None:
        """Xóa toàn bộ tệp đính kèm."""
        self._attached_files.clear()

    def build_message_payload(self, user_text: str) -> str:
        """
        Tổng hợp nội dung câu hỏi người dùng cùng toàn bộ tài liệu đính kèm thành prompt hoàn chỉnh.
        """
        user_text = user_text.strip()
        attached_files = list(self._attached_files)

        if not attached_files:
            return user_text

        file_sections = []
        file_names = []
        for idx, path in enumerate(attached_files, 1):
            file_name = os.path.basename(path)
            file_names.append(file_name)
            success, content, err = read_document_file(path)
            if success:
                file_sections.append(
                    f"=== [Tệp {idx}: {file_name}] ===\n{content}\n=== [Hết tệp {idx}] ==="
                )
            else:
                file_sections.append(
                    f"=== [Tệp {idx}: {file_name} - Lỗi đọc: {err}] ==="
                )

        prompt_header = user_text if user_text else "Hãy đọc, phân tích và so sánh / tổng hợp nội dung các tệp tin này giúp tôi."
        files_list_str = ", ".join(file_names)
        final_message = (
            f"📎 [Đính kèm {len(attached_files)} tệp: {files_list_str}]\n\n"
            + "\n\n".join(file_sections)
            + f"\n\n{prompt_header}"
        )
        return final_message

    # ----------------------------------------------------
    # PHÁT HIỆN & ĐỊNH DẠNG MÔ HÌNH CỤC BỘ (LOCAL MODELS)
    # ----------------------------------------------------

    @property
    def selected_model(self) -> str:
        return self._selected_model

    @selected_model.setter
    def selected_model(self, model_name: str):
        self._selected_model = model_name

    def format_model_name(self, raw_name: str) -> str:
        """Chuẩn hóa tên thư mục / file model thành tên hiển thị thân thiện."""
        name = raw_name
        # Xử lý định dạng cache folder của HuggingFace: models--Org--RepoName
        if name.startswith("models--"):
            parts = name.split("--")
            if len(parts) >= 3:
                name = parts[2]
            elif len(parts) == 2:
                name = parts[1]

        if name.endswith(".gguf"):
            name = name[:-5]
        if "/" in name:
            name = name.split("/")[-1]

        for sub in ["-Instruct", "-GGUF", "-gguf", "-Chat", "-chat"]:
            name = name.replace(sub, "")

        name = name.replace("_", " ").replace("-", " ").strip()

        if "LFM" in name and "LFM " not in name:
            name = name.replace("LFM", "LFM ")

        return name if name else raw_name

    def scan_local_models(self) -> List[str]:
        """
        Quét thư mục lưu trữ mô hình và trả về danh sách tên các mô hình GGUF hợp lệ (> 10MB).
        """
        settings = load_user_settings()
        agent_dir = settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))

        models: List[str] = []
        MIN_MODEL_SIZE = 10 * 1024 * 1024  # Tối thiểu 10MB để loại bỏ các tệp rỗng / cache lỗi

        if not os.path.exists(agent_dir):
            return models

        for item in os.listdir(agent_dir):
            if item.startswith('.'):
                continue
            item_path = os.path.join(agent_dir, item)
            if os.path.isdir(item_path):
                # Kiểm tra thư mục có chứa tệp .gguf hợp lệ hay không
                has_valid_gguf = False
                for root, _, files in os.walk(item_path):
                    for f in files:
                        if f.endswith(".gguf"):
                            fp = os.path.join(root, f)
                            try:
                                if os.path.getsize(fp) >= MIN_MODEL_SIZE:
                                    has_valid_gguf = True
                                    break
                            except OSError:
                                pass
                    if has_valid_gguf:
                        break
                if has_valid_gguf:
                    models.append(self.format_model_name(item))
            elif item.endswith(".gguf"):
                try:
                    if os.path.getsize(item_path) >= MIN_MODEL_SIZE:
                        models.append(self.format_model_name(item))
                except OSError:
                    pass

        return models
