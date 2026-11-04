#include "mascot_window.h"
#include <cmath>
#include <sstream>

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "msimg32.lib")

using namespace Gdiplus;

MascotWindow::MascotWindow(HINSTANCE hInstance, IpcClient& ipc)
    : m_hInstance(hInstance),
      m_hWnd(NULL),
      m_ipc(ipc),
      m_x(100),
      m_y(100),
      m_size(120),
      m_visible(false),
      m_dragging(false),
      m_dragMoved(false),
      m_voiceState("ready"),
      m_isPlayingMusic(false),
      m_isSleeping(false),
      m_phase(0.0),
      m_frameIndex(0),
      m_timerId(0)
{
    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&m_gdiplusToken, &gdiplusStartupInput, NULL);
}

MascotWindow::~MascotWindow() {
    if (m_timerId) {
        KillTimer(m_hWnd, m_timerId);
    }
    if (m_hWnd) {
        DestroyWindow(m_hWnd);
    }
    GdiplusShutdown(m_gdiplusToken);
}

bool MascotWindow::create(int x, int y, int size) {
    m_x = x;
    m_y = y;
    m_size = size;

    WNDCLASSEXA wc = {0};
    wc.cbSize = sizeof(WNDCLASSEXA);
    wc.style = CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS;
    wc.lpfnWndProc = MascotWindow::WndProc;
    wc.hInstance = m_hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_HAND);
    wc.lpszClassName = "PopNativeMascotClass";

    RegisterClassExA(&wc);

    m_hWnd = CreateWindowExA(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
        wc.lpszClassName,
        "POP Mini Mascot Native",
        WS_POPUP,
        m_x, m_y, m_size, m_size,
        NULL, NULL, m_hInstance, this
    );

    if (!m_hWnd) return false;

    // 45 - 60 FPS Animation Timer (approx 16-22 ms)
    m_timerId = SetTimer(m_hWnd, 1, 20, NULL);
    snapToEdgeIfNear();
    renderFrame();

    return true;
}

LRESULT CALLBACK MascotWindow::WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    MascotWindow* pThis = NULL;
    if (message == WM_NCCREATE) {
        CREATESTRUCTA* pCreate = (CREATESTRUCTA*)lParam;
        pThis = (MascotWindow*)pCreate->lpCreateParams;
        SetWindowLongPtrA(hWnd, GWLP_USERDATA, (LONG_PTR)pThis);
    } else {
        pThis = (MascotWindow*)GetWindowLongPtrA(hWnd, GWLP_USERDATA);
    }

    if (pThis) {
        return pThis->handleMessage(message, wParam, lParam);
    }
    return DefWindowProcA(hWnd, message, wParam, lParam);
}

LRESULT MascotWindow::handleMessage(UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_TIMER:
        m_phase += 0.08;
        renderFrame();
        return 0;

    case WM_LBUTTONDOWN:
        m_dragging = true;
        m_dragMoved = false;
        SetCapture(m_hWnd);
        GetCursorPos(&m_dragStartMouse);
        m_dragStartWindow.x = m_x;
        m_dragStartWindow.y = m_y;
        return 0;

    case WM_MOUSEMOVE:
        if (m_dragging) {
            POINT curMouse;
            GetCursorPos(&curMouse);
            int dx = curMouse.x - m_dragStartMouse.x;
            int dy = curMouse.y - m_dragStartMouse.y;
            if (abs(dx) > 3 || abs(dy) > 3) {
                m_dragMoved = true;
                m_x = m_dragStartWindow.x + dx;
                m_y = m_dragStartWindow.y + dy;
                SetWindowPos(m_hWnd, HWND_TOPMOST, m_x, m_y, m_size, m_size, SWP_NOSIZE | SWP_NOACTIVATE);
            }
        }
        return 0;

    case WM_LBUTTONUP:
        if (m_dragging) {
            m_dragging = false;
            ReleaseCapture();
            if (m_dragMoved) {
                snapToEdgeIfNear();
                // Notify Python about new position
                std::ostringstream ss;
                ss << "{\"event\":\"position_changed\",\"x\":" << m_x << ",\"y\":" << m_y << "}";
                m_ipc.sendMessage(ss.str());
            } else {
                // Single Click -> Toggle Mic
                m_ipc.sendMessage("{\"event\":\"toggle_mic\"}");
            }
        }
        return 0;

    case WM_LBUTTONDBLCLK:
        // Double Click -> Toggle Chat Window
        m_ipc.sendMessage("{\"event\":\"toggle_main_window\"}");
        return 0;

    case WM_RBUTTONUP:
        // Right Click -> Open Collection Dialog
        m_ipc.sendMessage("{\"event\":\"open_collection\"}");
        return 0;

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(m_hWnd, message, wParam, lParam);
}

void MascotWindow::renderFrame() {
    if (!m_hWnd) return;

    Bitmap bmp(m_size, m_size, PixelFormat32bppARGB);
    Graphics g(&bmp);
    g.SetSmoothingMode(SmoothingModeAntiAlias);
    g.SetInterpolationMode(InterpolationModeHighQualityBicubic);

    float cx = m_size / 2.0f;
    float cy = m_size / 2.0f;

    // Check which image to draw
    Bitmap* activeBmp = NULL;
    if (m_isPlayingMusic && m_musicBitmap) {
        activeBmp = m_musicBitmap.get();
    } else if (m_voiceState == "speaking" && m_talkBitmap) {
        activeBmp = m_talkBitmap.get();
    } else if (m_idleBitmap) {
        activeBmp = m_idleBitmap.get();
    }

    if (activeBmp) {
        // Subtle floating / breathing animation
        float bob = (float)(sin(m_phase * 2.0) * 2.5);
        float destW = 100.0f;
        float destH = 100.0f;
        float destX = cx - destW / 2.0f;
        float destY = cy - destH / 2.0f + bob;

        // Ground shadow
        SolidBrush shadowBrush(Color(45, 10, 10, 20));
        g.FillEllipse(&shadowBrush, cx - 30.0f, cy + 38.0f, 60.0f, 10.0f);

        // Character Sprite
        g.DrawImage(activeBmp, destX, destY, destW, destH);
    } else {
        // Default Procedural Cute Cyber-Pet when no PNG loaded
        float pulse = (float)((sin(m_phase * 2.5) + 1.0) / 2.0);
        SolidBrush bodyBrush(Color(255, 30, 35, 48));
        Pen outlinePen(Color(255, 56, 189, 248), 2.5f);
        g.FillEllipse(&bodyBrush, 15.0f, 15.0f, 90.0f, 90.0f);
        g.DrawEllipse(&outlinePen, 15.0f, 15.0f, 90.0f, 90.0f);

        // Cyber eyes
        SolidBrush eyeBrush(Color(255, 34, 211, 238));
        g.FillEllipse(&eyeBrush, 36.0f, 44.0f, 14.0f, 16.0f);
        g.FillEllipse(&eyeBrush, 70.0f, 44.0f, 14.0f, 16.0f);

        // Arc reactor heart
        SolidBrush heartBrush(Color(255, 244, 63, 94));
        g.FillEllipse(&heartBrush, cx - 6.0f + pulse, cy + 12.0f, 12.0f, 12.0f);
    }

    updateWindowBitmap(&bmp);
}

void MascotWindow::updateWindowBitmap(Bitmap* bmp) {
    HDC screenDc = GetDC(NULL);
    HDC memDc = CreateCompatibleDC(screenDc);

    HBITMAP hBitmap = NULL;
    bmp->GetHBITMAP(Color(0, 0, 0, 0), &hBitmap);
    HBITMAP oldBmp = (HBITMAP)SelectObject(memDc, hBitmap);

    SIZE wndSize = { m_size, m_size };
    POINT srcPoint = { 0, 0 };
    POINT destPoint = { m_x, m_y };

    BLENDFUNCTION blend = { 0 };
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;

    UpdateLayeredWindow(
        m_hWnd, screenDc,
        &destPoint, &wndSize,
        memDc, &srcPoint,
        0, &blend, ULW_ALPHA
    );

    SelectObject(memDc, oldBmp);
    DeleteObject(hBitmap);
    DeleteDC(memDc);
    ReleaseDC(NULL, screenDc);
}

void MascotWindow::loadCharacterSkin(const std::string& skinDir) {
    m_skinDir = skinDir;
    m_idleBitmap.reset();
    m_talkBitmap.reset();
    m_musicBitmap.reset();

    if (skinDir.empty()) return;

    std::wstring wDir(skinDir.begin(), skinDir.end());
    std::wstring idlePath = wDir + L"\\idle.png";
    std::wstring talkPath = wDir + L"\\talk.png";
    std::wstring musicPath = wDir + L"\\music.png";

    m_idleBitmap = std::make_unique<Bitmap>(idlePath.c_str());
    m_talkBitmap = std::make_unique<Bitmap>(talkPath.c_str());
    m_musicBitmap = std::make_unique<Bitmap>(musicPath.c_str());
}

void MascotWindow::snapToEdgeIfNear() {
    RECT workArea;
    SystemParametersInfoA(SPI_GETWORKAREA, 0, &workArea, 0);

    const int threshold = 40;
    if (m_x < workArea.left + threshold) m_x = workArea.left;
    if (m_x + m_size > workArea.right - threshold) m_x = workArea.right - m_size;
    if (m_y < workArea.top + threshold) m_y = workArea.top;
    if (m_y + m_size > workArea.bottom - threshold) m_y = workArea.bottom - m_size;

    SetWindowPos(m_hWnd, HWND_TOPMOST, m_x, m_y, m_size, m_size, SWP_NOSIZE | SWP_NOACTIVATE);
}

void MascotWindow::setVoiceState(const std::string& state) {
    m_voiceState = state;
}

void MascotWindow::setCharacter(const std::string& id, const std::string& skinDir) {
    m_characterId = id;
    loadCharacterSkin(skinDir);
}

void MascotWindow::setMusicMode(bool playing) {
    m_isPlayingMusic = playing;
}

void MascotWindow::wakeUp() {
    m_isSleeping = false;
}

void MascotWindow::setVisible(bool visible) {
    m_visible = visible;
    ShowWindow(m_hWnd, visible ? SW_SHOWNOACTIVATE : SW_HIDE);
}

void MascotWindow::moveTo(int x, int y) {
    m_x = x;
    m_y = y;
    SetWindowPos(m_hWnd, HWND_TOPMOST, m_x, m_y, m_size, m_size, SWP_NOSIZE | SWP_NOACTIVATE);
}

void MascotWindow::runMessageLoop() {
    MSG msg;
    while (GetMessageA(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
}

