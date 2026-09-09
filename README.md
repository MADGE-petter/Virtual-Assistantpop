# POP Assistant (POP AI)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![LLM](https://img.shields.io/badge/Local_LLM-LiquidAI_LFM2.5-FF6F00?style=for-the-badge&logo=huggingface&logoColor=white)
![GGUF](https://img.shields.io/badge/Inference-llama.cpp-00599C?style=for-the-badge)
![Voice](https://img.shields.io/badge/Voice-Sherpa--ONNX-00FFAA?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)

**Trợ lý ảo cá nhân thông minh thế hệ mới dành cho Windows — Kết hợp Local LLM, Voice Pipeline ngoại tuyến, Tự động hóa hệ thống và Giao diện hiện đại phong cách Gemini.**

</div>

---

## Giới thiệu

**POP Assistant** là ứng dụng trợ lý ảo desktop toàn diện được xây dựng bằng **Python** và **PyQt6**, tối ưu hóa cho Windows 10/11. Ứng dụng mang đến trải nghiệm tương tác tự nhiên qua giọng nói hoặc văn bản, chạy mô hình ngôn ngữ lớn (Local LLM) trực tiếp trên máy người dùng bảo đảm riêng tư dữ liệu 100%, đồng thời tích hợp khả năng điều khiển hệ thống và giám sát phần cứng thời gian thực.

---

## Tính năng nổi bật

### 1. Trải nghiệm Chat phong cách Gemini hiện đại
* **Giao diện khởi đầu Gemini**: Khi chưa có tin nhắn, thanh chat cùng dòng chào mừng cá nhân hóa (*"Xin chào, {Tên}! Tôi có thể giúp gì cho bạn hôm nay?"*) được căn giữa cân đối ở trung tâm màn hình.
* **Hiệu ứng Animation rơi mượt mà**: Khi gửi câu hỏi đầu tiên, dòng chữ mờ dần và thanh chat trượt êm ái xuống đáy màn hình (`400ms OutCubic`).
* **Starfield Canvas**: Nền vũ trụ sao lấp lánh nhẹ nhàng, tự động dừng render khi ẩn cửa sổ để tiết kiệm tài nguyên CPU/GPU.
* **Human-in-the-loop Action Cards**: Thẻ xác nhận tương tác trực quan trước khi thực thi các tác vụ hệ thống nhạy cảm (mở file, chạy ứng dụng, xóa dữ liệu).
* **Card xem trước tệp tin (File Preview)**: Hiển thị kết quả tìm kiếm file trong máy dạng thẻ kèm nút mở nhanh.

### 2. Local & Cloud AI Đa mô hình
* **Mô hình cục bộ mặc định**: Hỗ trợ dòng **LiquidAI LFM2.5 (2.6B / 7B)** định dạng **GGUF** qua `llama-cpp-python`.
* **Tăng tốc phần cứng**: Tự động tận dụng NVIDIA GPU qua CUDA hoặc chạy tối ưu trên CPU đa luồng.
* **Tích hợp Cloud Models**: Hỗ trợ chuyển đổi linh hoạt sang GPT-4o Mini hoặc Claude 3.5 Sonnet.
* **Bộ tải mô hình tích hợp (Model Downloader)**: Tải trực tiếp các mô hình AI từ Hugging Face với đa dạng mức lượng tử hóa (Q4_K_M, Q5_K_M, Q8_0,...).

### 3. Pipeline Giọng nói Ngoại tuyến (Offline Voice)
* **Nhận diện từ đánh thức (Wake Word)**: Tích hợp `OpenWakeWord` nhận diện từ khóa kích hoạt với độ trễ thấp.
* **Nhận dạng giọng nói (STT)**: Chuyển đổi giọng nói tiếng Việt thành văn bản ngoại tuyến qua `Sherpa-ONNX`.
* **Tổng hợp tiếng nói (TTS)**: Phản hồi bằng giọng nói tự nhiên, mượt mà không cần kết nối Internet.
* **Mini Mascot lơ lửng (Floating Avatar)**: Widget linh vật nhỏ gọn ngoài màn hình: click 1 chạm để bật/tắt micro, nhấp đúp để mở/thu gọn cửa sổ chat chính.

### 4. Tự động hóa & Điều khiển Windows
* Quét, tìm kiếm và mở nhanh các ứng dụng đã cài đặt trên Windows.
* Điều chỉnh âm lượng hệ thống qua `PyCaw`.
* Tinh chỉnh độ sáng màn hình laptop/PC.
* Truy xuất thông tin phần cứng qua Windows WMI.
* **Dịch vụ chủ động (Proactive Service) & Ghi nhớ thói quen (Habit Tracker)**: Học thói quen sử dụng phần mềm của người dùng và đưa ra gợi ý thông minh.

### 5. Bảng Giám sát Phần cứng Thời gian thực (System Telemetry)
* Giám sát tài nguyên phần cứng: CPU, RAM, Disk, Pin qua `psutil`.
* Đo lường GPU NVIDIA: % Sử dụng GPU, VRAM và Nhiệt độ GPU tức thời thông qua `PyNVML`.
* Bộ đo sóng âm giọng nói (Audio Waveform Visualizer) hiển thị trạng thái lắng nghe.
* Nhật ký hoạt động hệ thống (Activity Logs).

### 6. Trung tâm Cài đặt Chuyên sâu (Settings Hub)
* **General**: Tùy chỉnh âm thanh, khởi động cùng Windows, phím tắt.
* **Models**: Quản lý model, chỉ định thư mục lưu trữ, lượng tử hóa.
* **Profile**: Cập nhật tên hiển thị, hình đại diện và sở thích cá nhân.
* **Rules**: Tùy biến System Prompt, Persona và quy tắc ứng xử của trợ lý.
* **Database**: Xem và quản lý lịch sử hội thoại, dọn dẹp bộ nhớ SQLite.
* **Download**: Quản lý tải xuống các model AI mới.
* **About**: Thông tin phiên bản, bản quyền và chẩn đoán phần cứng.

---

## Kiến trúc Hệ thống

Dự án áp dụng chặt chẽ mô hình **MVC (Model - View - Controller)** kết hợp **Modular Coordinator & Service Layer**:

```text
               ┌──────────────────────────────┐
               │    Desktop View (PyQt6)      │
               │  PopView • MiniMascotWidget  │
               └──────────────┬───────────────┘
                              │ Signals / Slots
                              ▼
               ┌──────────────────────────────┐
               │        PopController         │
               │      (Facade Controller)     │
               └──────────────┬───────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│StartupCoordinator│ │ConversationCoord.│ │VoiceModeCoord.   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         └────────────────────┼────────────────────┘
                              ▼
               ┌──────────────────────────────┐
               │        Service Layer         │
               │ ├── Audio / Voice Service    │
               │ ├── LLMService (Local/Cloud) │
               │ ├── SystemMonitoringService  │
               │ ├── ActionHandler / AppScan  │
               │ └── Proactive & Habit Service│
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    Data / Storage Layer      │
               │  SQLite DB • Memory • Cache  │
               └──────────────────────────────┘
```

---

## Yêu cầu Hệ thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10 / 11 64-bit | Windows 11 64-bit |
| **Python** | Python 3.9 - 3.12 | Python 3.11 |
| **RAM** | 8 GB | 16 GB hoặc cao hơn |
| **GPU** | Tùy chọn (chạy CPU) | NVIDIA GPU (>= 4GB VRAM) hỗ trợ CUDA |
| **Âm thanh** | Microphone & Loa ngoài | Headset có khử ồn |

---

## Hướng dẫn Cài đặt & Khởi chạy

### 1. Clone mã nguồn
```bash
git clone https://github.com/MADGE-petter/Virtual-Assistantpop.git
cd Virtual-Assistantpop
```

### 2. Cài đặt các thư viện phụ thuộc
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!NOTE]
> Nếu bạn sở hữu card đồ họa NVIDIA và muốn kích hoạt tăng tốc CUDA cho Local LLM, hãy cài đặt bản `llama-cpp-python` hỗ trợ CUDA:
> ```bash
> pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
> ```

### 3. Khởi chạy ứng dụng
Chạy màn hình đăng nhập / khởi động ứng dụng:
```bash
python login.py
```
* Sau khi đăng nhập thành công, ứng dụng sẽ xuất hiện dưới dạng **Mini Mascot** tròn lơ lửng góc màn hình.
* **Bấm đúp (Double-click)** vào Mini Mascot để mở giao diện chat đầy đủ phong cách Gemini.

---

## Cấu trúc Thư mục Dự án

```text
Virtual-Assistantpop/
├── controller/                 # Bộ điều khiển MVC & các Coordinators
│   ├── pop_controller.py       # Facade Controller trung tâm
│   ├── startup_coordinator.py  # Khởi động bất đồng bộ (<0.1s)
│   ├── conversation_coordinator.py
│   ├── voice_mode_coordinator.py
│   └── handlers/               # Xử lý hành động hệ thống & ứng dụng
├── model/                      # Các mô hình dữ liệu (Chat, System, SQL)
│   ├── pop_chat_model.py
│   ├── system_monitor_model.py
│   └── Sql.py
├── service/                    # Lớp dịch vụ nghiệp vụ
│   ├── AudioService.py         # Âm thanh, STT, TTS
│   ├── llm_service.py          # Kết nối Local LLM (llama.cpp) & Cloud API
│   ├── system_monitoring_service.py # Theo dõi CPU, GPU, RAM
│   ├── voice_service.py        # Quản lý nhận diện giọng nói
│   └── proactive_service.py    # Gợi ý thông minh theo ngữ cảnh
├── view/                       # Giao diện người dùng PyQt6
│   ├── ui/
│   │   ├── pop_view.py         # Cửa sổ chính POP View
│   │   ├── icons.py            # Vector icons & logo rendering
│   │   ├── styles.py           # Design tokens, màu sắc, QSS
│   │   ├── settings/           # Các tab trong cửa sổ Cài đặt
│   │   └── widgets/
│   │       ├── chat_area_widget.py       # Khu vực chat trung tâm & animation
│   │       ├── input_bar_widget.py       # Thanh chat viền phát sáng
│   │       ├── mini_mascot_widget.py     # Mascot lơ lửng ngoài desktop
│   │       ├── right_panel_widget.py     # Giám sát phần cứng & telemetry
│   │       ├── sidebar_widget.py         # Danh sách hội thoại & chuyển tab
│   │       └── starfield_widget.py       # Nền bầu trời sao chuyển động
├── LLM-agents/                 # Thư mục chứa các mô hình GGUF cục bộ
├── assets/                     # Hình ảnh, âm thanh, icon tĩnh
├── login.py                    # Điểm khởi đầu đăng nhập & mở ứng dụng
└── main.py                     # Entry point khởi tạo giao diện chính
```

---

## Đóng góp & Phát triển

Mọi đóng góp, báo lỗi (Issue) hoặc đề xuất tính năng mới (Pull Request) đều được hoan nghênh:
1. Fork repository.
2. Tạo branch tính năng (`git checkout -b feature/AmazingFeature`).
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`).
4. Push lên branch (`git push origin feature/AmazingFeature`).
5. Tạo Pull Request.

---

## Bản quyền

Dự án được phát hành dưới bản quyền mở. Mọi quyền sở hữu thuộc về nhóm phát triển **MADGE-petter / POP AI Assistant**.
