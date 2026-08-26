# Pop Assistant

**Pop Assistant** là trợ lý ảo cá nhân chạy trên Windows, được phát triển bằng **Python và PyQt6**. Dự án tích hợp xử lý giọng nói, Local LLM, điều khiển hệ thống Windows và giám sát phần cứng trong một ứng dụng desktop.

## Tính năng chính

* **Voice Assistant**

  * Wake Word Detection với `OpenWakeWord`
  * Speech-to-Text với `Sherpa-ONNX`
  * Text-to-Speech với `Sherpa-ONNX`
  * Xử lý audio với `PyAudio`, `SoundDevice`, `SoundFile`, `Librosa`
  * Phân loại và xử lý câu lệnh

* **Local AI**

  * Sử dụng **LiquidAI LFM2.5-2.6B** làm Local LLM
  * Model chạy ở định dạng **GGUF**
  * Inference thông qua `llama-cpp-python`
  * Hỗ trợ CPU và NVIDIA GPU
  * Có thể sử dụng CUDA để tăng tốc suy luận

* **Windows Automation**

  * Quét và mở ứng dụng
  * Điều khiển âm lượng với `PyCaw`
  * Điều khiển độ sáng màn hình
  * Truy xuất thông tin hệ thống thông qua `WMI`

* **Hardware Monitoring**

  * CPU, RAM, Disk và Battery với `Psutil`
  * NVIDIA GPU và VRAM với `NVML`
  * Theo dõi thông tin phần cứng Windows
  * Hệ thống cảnh báo và giám sát

* **Application & Data**

  * Theo dõi lịch sử sử dụng ứng dụng
  * Quản lý hội thoại
  * SQLite Database
  * Habit Tracking và Recommendation

## Kiến trúc

Dự án sử dụng **MVC kết hợp Service Layer**.

```text
User
 │
 ▼
View - PyQt6
 │
 ▼
Controller
 │
 ▼
Service Layer
 ├── Voice / Audio
 ├── Local LLM
 ├── Intent Processing
 ├── System Monitoring
 ├── Windows Control
 ├── App Scanner
 ├── Conversation
 └── Alert / Recommendation
 │
 ▼
Model / SQLite
```

### Voice & AI Pipeline

```text
Microphone
    │
    ▼
OpenWakeWord
    │
    ▼
Sherpa-ONNX ASR
    │
    ▼
Intent / Command Processing
    │
    ├──────────────┐
    │              │
    ▼              ▼
System Action   LFM2.5-2.6B
                    │
                    ▼
              llama-cpp-python
                    │
                    ▼
              Response
    │              │
    └───────┬──────┘
            ▼
      Sherpa-ONNX TTS
            │
            ▼
         Speaker
```

## Công nghệ nổi bật

| Công nghệ                     | Vai trò                         |
| ----------------------------- | ------------------------------- |
| **Python**                    | Ngôn ngữ phát triển             |
| **PyQt6**                     | Desktop GUI                     |
| **Sherpa-ONNX**               | Speech-to-Text / Text-to-Speech |
| **OpenWakeWord**              | Wake Word Detection             |
| **LiquidAI LFM2.5-2.6B**      | Local Language Model            |
| **GGUF**                      | Định dạng model                 |
| **llama-cpp-python**          | Local LLM inference             |
| **Hugging Face Hub**          | Model management                |
| **CUDA**                      | GPU acceleration                |
| **PyAudio / SoundDevice**     | Audio input/output              |
| **Librosa / SoundFile**       | Audio processing                |
| **Psutil**                    | System monitoring               |
| **WMI**                       | Windows system information      |
| **PyNVML / NVML**             | NVIDIA GPU monitoring           |
| **PyCaw**                     | Windows audio control           |
| **Comtypes**                  | Windows API integration         |
| **Screen Brightness Control** | Display brightness              |
| **SQLite**                    | Local data storage              |
| **PyInstaller**               | Windows packaging               |

## Local AI

Pop Assistant sử dụng **LiquidAI LFM2.5-2.6B** làm mô hình ngôn ngữ cục bộ.

Model được chạy dưới dạng GGUF thông qua `llama-cpp-python`, cho phép inference trực tiếp trên máy người dùng. Liquid AI cung cấp các phiên bản GGUF với nhiều mức quantization như Q4, Q5, Q6 và Q8 để cân bằng giữa chất lượng, bộ nhớ và tốc độ suy luận.

Ví dụ cấu hình model:

```text
LLM-agents/
└── LFM2.5-2.6B-*.gguf
```

Kiến trúc này cho phép Pop Assistant sử dụng Local LLM mà không cần phụ thuộc hoàn toàn vào API cloud.

## Yêu cầu

* Windows 10/11 64-bit
* Python >= 3.9
* RAM tối thiểu 8 GB
* 16 GB RAM khuyến nghị khi sử dụng Local LLM
* Microphone và Speaker
* NVIDIA GPU tùy chọn

## Cài đặt

```bash
git clone https://github.com/MADGE-petter/Virtual-Assistantpop.git
cd Virtual-Assistantpop
pip install --upgrade pip
pip install -r requirements.txt
```
### Chạy

```bash
python login.py
```
## Trạng thái

* PyQt6 Desktop UI
* MVC + Service Layer
* OpenWakeWord
* Sherpa-ONNX Voice Pipeline
* LiquidAI LFM2.5-2.6B Local LLM
* GGUF + llama.cpp inference
* CUDA acceleration
* Windows System Control
* NVIDIA GPU Monitoring
* Application Management
* Usage Tracking
* SQLite Database
* PyInstaller Packaging
