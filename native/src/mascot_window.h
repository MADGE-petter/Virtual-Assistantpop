#pragma once

#include <windows.h>
#include <gdiplus.h>
#include <string>
#include <vector>
#include <memory>
#include "ipc_client.h"

class MascotWindow {
public:
    MascotWindow(HINSTANCE hInstance, IpcClient& ipc);
    ~MascotWindow();

    bool create(int x = 100, int y = 100, int size = 120);
    void runMessageLoop();

    void setVoiceState(const std::string& state);
    void setCharacter(const std::string& id, const std::string& skinDir);
    void setMusicMode(bool playing);
    void wakeUp();
    void setVisible(bool visible);
    void moveTo(int x, int y);

private:
    static LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam);
    LRESULT handleMessage(UINT message, WPARAM wParam, LPARAM lParam);

    void renderFrame();
    void updateWindowBitmap(Gdiplus::Bitmap* bmp);
    void loadCharacterSkin(const std::string& skinDir);
    void snapToEdgeIfNear();

    HINSTANCE m_hInstance;
    HWND m_hWnd;
    IpcClient& m_ipc;

    int m_x;
    int m_y;
    int m_size;
    bool m_visible;
    bool m_dragging;
    bool m_dragMoved;
    POINT m_dragStartMouse;
    POINT m_dragStartWindow;

    std::string m_voiceState;
    std::string m_characterId;
    std::string m_skinDir;
    bool m_isPlayingMusic;
    bool m_isSleeping;

    // GDI+ tokens & cached images
    ULONG_PTR m_gdiplusToken;
    std::vector<std::unique_ptr<Gdiplus::Bitmap>> m_idleFrames;
    std::vector<std::unique_ptr<Gdiplus::Bitmap>> m_talkFrames;
    std::vector<std::unique_ptr<Gdiplus::Bitmap>> m_dragFrames;
    std::vector<std::unique_ptr<Gdiplus::Bitmap>> m_musicFrames;
    std::unique_ptr<Gdiplus::Bitmap> m_idleBitmap;
    std::unique_ptr<Gdiplus::Bitmap> m_talkBitmap;
    std::unique_ptr<Gdiplus::Bitmap> m_musicBitmap;

    double m_phase;
    int m_frameIndex;
    UINT_PTR m_timerId;
};

