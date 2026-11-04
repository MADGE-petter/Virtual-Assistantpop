# POP Assistant (POP AI)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-17-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![LLM](https://img.shields.io/badge/Local_LLM-GGUF_Inference-FF6F00?style=for-the-badge&logo=huggingface&logoColor=white)
![Voice](https://img.shields.io/badge/ASR%2FTTS-Sherpa--ONNX%20%7C%20MeloTTS-00FFAA?style=for-the-badge)
![Audio](https://img.shields.io/badge/WASAPI-Low_Latency-blueviolet?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)

**Trợ lý ảo cá nhân thông minh thế hệ mới dành cho Windows — Kiến trúc Hybrid kết hợp Python & C++ Native Core, Offline Voice Pipeline, Local LLM GGUF, và Hệ thống Mascot Gacha đa nhân vật.**

[Tính năng nổi bật](#-tính-năng-nổi-bật) • [Kiến trúc Hybrid](#-kiến-trúc-hệ-thống-hybrid-architecture) • [Bộ sưu tập Mascot](#-hệ-thống-mascot--gacha-bộ-sưu-tập) • [Cài đặt & Khởi chạy](#-hướng-dẫn-cài-đặt--khởi-chạy) • [Đóng gói EXE](#-đóng-gói-ứng-dụng-thành-file-exe)

</div>

---

## 🌟 Giới thiệu

**POP Assistant** là ứng dụng trợ lý ảo máy tính toàn diện được thiết kế chuyên biệt cho hệ điều hành **Windows 10/11**. Dự án vận hành theo mô hình **Hybrid Architecture**:
- **Tầng ứng dụng (Python & PyQt6)**: Quản lý nghiệp vụ, giao diện chat phong cách Gemini, điều khiển hệ thống, quản lý cơ sở dữ liệu SQLite và tích hợp AI.
- **Tầng hiệu năng cao (C++ Native Core)**: Thu âm micro qua Windows WASAPI với độ trễ thấp (<10ms), bộ tách câu streaming thời gian thực (Time-to-First-Voice < 500ms), ngắt giọng tức thì (Full-Duplex Barge-in), và render Mascot độc lập siêu nhẹ.

Toàn bộ mô hình ngôn ngữ lớn (LLM), nhận dạng giọng nói (ASR) và tổng hợp tiếng nói (TTS) đều chạy **100% cục bộ (Offline)**, đảm bảo quyền riêng tư dữ liệu tuyệt đối và không phụ thuộc vào kết nối Internet.

---

## 🚀 Tính năng nổi bật

### 1. Trải nghiệm Chat thông minh & Giao diện vũ trụ hiện đại
* **Giao diện khởi đầu phong cách Gemini**: Khi chưa có tin nhắn, thanh chat cùng lời chào cá nhân hóa được căn giữa trang nhã ở trung tâm màn hình. Khi gửi câu hỏi đầu tiên, thanh chat tự động lướt xuống đáy với hiệu ứng `OutCubic 400ms`.
* **Cosmic Canvas (Starfield)**: Nền bầu trời sao chuyển động êm ái, tự động tạm dừng render khi ẩn cửa sổ để tối ưu hóa 0% CPU/GPU.
* **Human-in-the-loop Action Cards**: Thẻ xác nhận tương tác trực quan trước khi thực thi các tác vụ hệ thống (mở file, khởi chạy ứng dụng, duyệt web).
* **Card xem trước tệp tin (File Preview)**: Trình duyệt và tìm kiếm file nhanh trong máy dạng thẻ kèm nút mở trực tiếp.

### 2. Tầng Voice Pipeline ngoại tuyến & C++ Native Engine
* **Thu âm WASAPI độ trễ thấp**: Bắt luồng âm thanh micro trực tiếp qua Windows Core Audio ở tầng kernel, tự động chuyển đổi sang chuẩn `16kHz 16-bit Mono PCM`.
* **Streaming Sentence Chunking**: Bóc tách câu theo thời gian thực ngay khi LLM đang sinh token. Đẩy ngay câu đầu tiên sang TTS phát âm thanh tức thì mà không cần đợi sinh hết đoạn văn bản.
* **Full-Duplex Barge-in (Ngắt thông minh)**: Khi trợ lý đang nói chuyện, nếu người dùng cất giọng nói chen vào, WASAPI sẽ phát hiện ngưỡng năng lượng âm thanh và kích hoạt ngắt tức thì (`sd.stop()`), lập tức chuyển về trạng thái lắng nghe.
* **ASR Việt hóa (Sherpa-ONNX Zipformer)**: Nhận dạng giọng nói tiếng Việt chính xác cao, hoàn toàn offline trên CPU/GPU.
* **TTS Tự nhiên (MeloTTS VITS-2)**: Giọng đọc tiếng Việt truyền cảm, hỗ trợ biến đổi cao độ (pitch-shift) và timbre giọng nói riêng cho từng nhân vật.

### 3. Hệ sinh thái Local LLM (GGUF Engine)
* **Tương thích toàn diện llama.cpp**: Hỗ trợ mọi dòng mô hình định dạng `.gguf` phổ biến (LiquidAI LFM2.5/LFM3, Llama 3.2, Qwen 2.5, DeepSeek, Mistral, Gemma 2,...).
* **Tự động tối ưu luồng CPU & Tăng tốc GPU**: Tự động nhận diện số nhân CPU tối ưu (tránh tình trạng khóa 100% CPU gây giật lag hệ thống), hỗ trợ offload layer lên NVIDIA GPU qua CUDA.
* **Chợ Model Hugging Face (Model Hub)**: Tìm kiếm và tải trực tiếp hàng ngàn model GGUF từ Hugging Face Hub, tự động đối chiếu thông tin phần cứng (VRAM, RAM khả dụng) để khuyên dùng mức Quantization (Q4_K_M, Q5_K_M, Q8_0) mượt mà nhất.

### 4. Tự động hóa & Giám sát hệ thống Windows
* **Điều khiển hệ thống**: Tăng giảm âm lượng qua `PyCaw`, điều chỉnh độ sáng màn hình laptop, quét và khởi chạy ứng dụng cài sẵn trong máy.
* **Bảng giám sát phần cứng (Hardware Telemetry)**: Đo lường thời gian thực mức sử dụng CPU, RAM, Disk, Pin qua `psutil`, đo nhiệt độ và % VRAM card đồ họa NVIDIA qua `PyNVML`.
* **Học thói quen (Habit Tracker)**: Ghi nhớ thói quen mở phần mềm theo khung giờ và gợi ý mở chủ động.

---

## 🎭 Hệ thống Mascot & Gacha Bộ sưu tập

Ứng dụng sở hữu hệ thống linh vật lơ lửng ngoài màn hình (Desktop Mascot) đi kèm tính năng **Gacha quay thưởng thẻ bài** độc đáo:

```
[Mascot Ngoài Màn Hình] ──(Chuột phải)──> [Bộ Sưu Tập & Gacha] ──(Tích luỹ)──> [Pop Coins]
```

### Danh sách nhân vật độc quyền:
| Nhân vật | Độ hiếm | Đặc điểm & Giọng lồng tiếng |
| :--- | :---: | :--- |
| **Pop Chibi** | `Common` | Linh vật tròn nguyên bản, mắt chớp biểu cảm, phản ứng theo âm thanh micro. |
| **Phoebe Chupi** | `Rare` | Bé cánh cụt hoạt bát, giọng lồng tiếng Chupi cao vút đáng yêu (`452Hz`). |
| **Nono Mũm Mĩm** | `Epic` | Nono mập mạp, giọng lồng tiếng tự nhiên tách biệt 2 cụm: nói (`talk.wav`) và đánh thức (`wake.wav`). |
| **Aemeath Idol** | `Legendary` | Nữ thần tượng âm nhạc, giọng nói ngọt ngào ấm áp (`440Hz`). |
| **Phrolova Ponova** | `Mythic` (Đỏ) | Bộ animation kéo đàn violin phát nốt nhạc trong suốt 18 frames (`music.gif`), âm sắc huyền bí. |

* **Gacha Hộp Quà**: Sử dụng **Pop Coins** nhận được từ việc trò chuyện và tương tác với trợ lý để mở hòm gacha, sưu tầm skin và âm thanh độc quyền.

---

## 🏛 Kiến trúc Hệ thống (Hybrid Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                   C++ / Qt6 Native Core (High Performance)             │
│  ├── PopVoiceEngine.exe : WASAPI Mic Capture, Sentence Streamer, Barge-in│
│  └── PopMascotNative.exe: Direct2D / GDI+ Desktop Mascot (60 FPS)      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                   IPC (Windows Named Pipes)
                   ├── \\.\pipe\pop_voice_ipc
                   └── \\.\pipe\pop_mascot_ipc
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                    Python Application Layer (MVC)                      │
│  ├── PopController     : Facade Controller điều phối toàn bộ hệ thống │
│  ├── VoiceIpcBridge    : Cầu nối IPC C++ kèm Graceful Fallback Mode    │
│  ├── PopView           : Giao diện chính PyQt6 (Gemini Style + Starfield)│
│  ├── AudioService      : Runtime quản lý Sherpa-ONNX & MeloTTS        │
│  ├── LLMService        : Wrapper llama-cpp-python đa luồng            │
│  └── Storage / Database: SQLite, Bộ nhớ ngữ cảnh (MemoryService)       │
└────────────────────────────────────────────────────────────────────────┘
```

> [!TIP]
> **Cơ chế Graceful Fallback (Không gián đoạn)**: Khi chưa biên dịch file thực thi C++ `PopVoiceEngine.exe` hoặc `PopMascotNative.exe`, ứng dụng sẽ tự động chuyển đổi trong 0 giây sang chế độ **Python In-Process Fallback**, đảm bảo phần mềm luôn khởi chạy mượt mà không bao giờ gặp lỗi thiếu file.

---

## 💻 Yêu cầu Hệ thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10 / 11 64-bit | Windows 11 64-bit |
| **Python** | Python 3.10 – 3.12 | Python 3.11 |
| **RAM** | 8 GB RAM | 16 GB RAM trở lên |
| **GPU** | Tùy chọn (chạy mượt trên CPU) | NVIDIA GPU (>= 4GB VRAM) hỗ trợ CUDA |
| **C++ Compiler** | *(Tùy chọn khi build native)* | MSVC (Visual Studio 2019+) hoặc MinGW-w64 |
| **Âm thanh** | Micro và Loa ngoài | Tai nghe có chống ồn |

---

## 📦 Hướng dẫn Cài đặt & Khởi chạy

### 1. Tải mã nguồn
```bash
git clone -b Test-C https://github.com/MADGE-petter/Virtual-Assistantpop.git
cd Virtual-Assistantpop
```

### 2. Cài đặt môi trường Python
```bash
# Khuyến nghị tạo môi trường ảo
python -m venv venv
.\venv\Scripts\activate

# Cài đặt các thư viện cần thiết
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!NOTE]
> Để kích hoạt tăng tốc GPU NVIDIA CUDA cho mô hình LLM, cài đặt bản `llama-cpp-python` biên dịch sẵn:
> ```bash
> pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
> ```

### 3. (Tùy chọn) Biên dịch tầng C++ Native Core
Nếu máy bạn có cài sẵn **Visual Studio (MSVC)** hoặc **MinGW GCC**, bạn có thể biên dịch module C++ để kích hoạt hiệu năng tối đa:
```cmd
:: Biên dịch bộ điều phối Voice & WASAPI Engine
native\build_voice_engine.bat

:: Biên dịch Mascot Window Native siêu nhẹ
native\build_win32.bat
```
*(Nếu bỏ qua bước này, trợ lý vẫn hoạt động trơn tru qua chế độ Python Fallback tích hợp sẵn).*

### 4. Khởi chạy ứng dụng
```bash
python login.py
```
* Đăng nhập tài khoản hoặc tạo mới người dùng.
* Mascot chibi sẽ xuất hiện lơ lửng trên màn hình:
  - **Nhấp đơn (Click)**: Bật/Tắt Micro lắng nghe giọng nói.
  - **Chuột phải (Right-Click)**: Mở Kho đồ, Tủ đồ Mascot & Vòng quay Gacha.
  - **Kéo thả (Drag)**: Di chuyển vị trí và tự động hít bám vào cạnh màn hình.
  - **Bấm đúp (Double-Click)**: Mở / Ẩn cửa sổ Chat chính.

---

## 🔨 Đóng gói Ứng dụng thành file EXE

Dự án cung cấp sẵn kịch bản đóng gói ứng dụng thành file thực thi độc lập không cần cài đặt Python:

```bash
python build.py
```
Sau khi build hoàn tất, file thực thi sẽ nằm tại:
```text
dist/PopAssistant.exe
```

---

## 📁 Cấu trúc Thư mục Dự án

```text
Virtual-Assistantpop/
├── controller/                 # Bộ điều khiển trung tâm & các Coordinators
│   ├── pop_controller.py       # Facade Controller kết nối View, Voice, LLM
│   ├── startup_coordinator.py  # Khởi động bất đồng bộ
│   ├── conversation_coordinator.py # Điều phối phiên hội thoại
│   └── handlers/               # Xử lý ứng dụng, file, âm lượng, thời tiết
├── model/                      # Các mô hình dữ liệu (Chat, Telemetry, Database)
│   ├── pop_chat_model.py
│   ├── system_monitor_model.py
│   └── Sql.py
├── native/                     # Tầng mã nguồn C++ Native Core
│   ├── CMakeLists.txt          # Cấu hình build CMake
│   ├── build_voice_engine.bat  # Script build PopVoiceEngine.exe
│   ├── build_win32.bat         # Script build PopMascotNative.exe
│   └── src/
│       ├── voice/              # WASAPI audio capture, sentence streamer, orchestrator
│       └── mascot_window.cpp   # Render Mascot 60 FPS Win32
├── service/                    # Lớp dịch vụ nghiệp vụ
│   ├── AudioService.py         # Sherpa-ONNX ASR & MeloTTS
│   ├── voice_service.py        # Voice I/O và chu kỳ Sleep/Wake
│   ├── voice_ipc_bridge.py     # Cầu nối IPC C++ Voice Engine & Fallback
│   ├── llm_service.py          # Wrapper llama-cpp-python GGUF
│   ├── collection/             # Dịch vụ Gacha & Bộ sưu tập Mascot
│   └── system_monitoring_service.py
├── skins/                      # Thư viện Sprite Sheet & Animation Skin Mascot
│   ├── aemeath/
│   ├── nono/
│   ├── phoebe/
│   └── phrolova/               # Mythic transparent violin animated GIF
├── view/                       # Giao diện người dùng PyQt6
│   ├── ui/
│   │   ├── pop_view.py         # Cửa sổ chính POP AI View
│   │   ├── styles.py           # Design tokens, màu sắc vũ trụ
│   │   ├── mascot/             # Module Mini Mascot & Mascot IPC Bridge
│   │   ├── collection/         # Giao diện Tủ đồ & Vòng quay Gacha
│   │   └── settings/           # Các tab Cài đặt & Tải Model Hugging Face
├── voice-models/               # Model nhận dạng giọng nói offline (Zipformer)
├── build.py                    # Script đóng gói PyInstaller EXE
├── login.py                    # Điểm vào đăng nhập và khởi tạo
└── main.py                     # Entry point chính của ứng dụng
```

---

## 🤝 Đóng góp & Phát triển

Mọi đóng góp, báo lỗi (Issue) hoặc gửi bản vá (Pull Request) đều được hoan nghênh:
1. Fork repository.
2. Tạo nhánh tính năng (`git checkout -b feature/TenTinhNangMoi`).
3. Commit các thay đổi (`git commit -m 'feat: them tinh nang moi'`).
4. Push lên nhánh của bạn (`git push origin feature/TenTinhNangMoi`).
5. Tạo Pull Request trên GitHub.

---

<div align="center">
  <sub>Phát triển bởi đội ngũ POP AI Assistant • Dành riêng cho trải nghiệm máy tính Windows hiện đại.</sub>
</div>
