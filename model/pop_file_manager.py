import os
import platform
import subprocess


def open_file_or_directory(path: str):
   
    if not os.path.exists(path):
        return f"Lỗi: Đường dẫn '{path}' không tồn tại."

    if platform.system() == "Windows":
        try:
            os.startfile(path)
            return f"Đã mở '{path}'."
        except Exception as e:
            return f"Lỗi khi mở '{path}': {e}"
    elif platform.system() == "Darwin":  # macOS
        try:
            subprocess.run(["open", path])
            return f"Đã mở '{path}'."
        except Exception as e:
            return f"Lỗi khi mở '{path}': {e}"
    elif platform.system() == "Linux":
        try:
            subprocess.run(
                ["xdg-open", path]
            )  # Lệnh phổ biến trên nhiều bản phân phối Linux
            return f"Đã mở '{path}'."
        except Exception as e:
            return f"Lỗi khi mở '{path}': {e}"
    else:
        return "Hệ điều hành không được hỗ trợ để mở tệp/thư mục."


def list_directory_contents(path: str):
   
    if not os.path.exists(path):
        return f"Lỗi: Thư mục '{path}' không tồn tại."
    if not os.path.isdir(path):
        return f"Lỗi: '{path}' không phải là một thư mục."

    try:
        contents = os.listdir(path)
        if not contents:
            return f"Thư mục '{path}' trống."

        # Phân loại và hiển thị một cách thân thiện
        files = [f for f in contents if os.path.isfile(os.path.join(path, f))]
        dirs = [d for d in contents if os.path.isdir(os.path.join(path, d))]

        response = f"Nội dung của '{path}':\n"
        if dirs:
            response += "Thư mục: " + ", ".join(dirs) + "\n"
        if files:
            response += "Tệp: " + ", ".join(files) + "\n"
        return response.strip()

    except Exception as e:
        return f"Lỗi khi liệt kê nội dung thư mục '{path}': {e}"


if __name__ == "__main__":
    print("--- Thử nghiệm chức năng quản lý tệp và thư mục ---")

    # Mở một thư mục hiện có (ví dụ: thư mục dự án)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Thử mở thư mục hiện tại: {current_dir}")
    print(open_file_or_directory(current_dir))

    # Mở một tệp hiện có (ví dụ: POP.py)
    pop_file_path = os.path.join(current_dir, "POP.py")
    if os.path.exists(pop_file_path):
        print(f"\nThử mở tệp POP.py: {pop_file_path}")
        print(open_file_or_directory(pop_file_path))
    else:
        print(f"\nKhông tìm thấy tệp POP.py tại: {pop_file_path}")

    # Liệt kê nội dung thư mục hiện tại
    print(f"\nLiệt kê nội dung thư mục hiện tại: {current_dir}")
    print(list_directory_contents(current_dir))

    # Thử mở đường dẫn không tồn tại
    print("\nThử mở đường dẫn không tồn tại:")
    print(open_file_or_directory("C:\\duong_dan_khong_ton_tai"))

    # Thử liệt kê nội dung đường dẫn không tồn tại
    print("\nThử liệt kê nội dung đường dẫn không tồn tại:")
    print(list_directory_contents("C:\\thu_muc_khong_ton_tai"))

    # Thử liệt kê nội dung của một tệp (không phải thư mục)
    if os.path.exists(pop_file_path):
        print(f"\nThử liệt kê nội dung của tệp POP.py: {pop_file_path}")
        print(list_directory_contents(pop_file_path))
