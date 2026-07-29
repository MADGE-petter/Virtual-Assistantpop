#!/usr/bin/env python3
import re

# Đọc file
with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Thay thế phần hero-core
old_hero_core = '<div class="hero-core">\n            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
new_hero_core = '<div class="hero-core">\n            <div class="logo-container">\n            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" class="logo-svg">'

content = content.replace(old_hero_core, new_hero_core)

# Thêm class cho các phần tử SVG
content = content.replace(
    '<rect x="2" y="2" width="32" height="32" rx="8" fill="url(#heroGrad)" fill-opacity="0.15"/>',
    '<rect x="2" y="2" width="32" height="32" rx="8" fill="url(#heroGrad)" fill-opacity="0.15" class="logo-ring"/>'
)

content = content.replace(
    '<rect x="2" y="2" width="32" height="32" rx="8" stroke="url(#heroGrad)" stroke-width="2"/>',
    '<rect x="2" y="2" width="32" height="32" rx="8" stroke="url(#heroGrad)" stroke-width="2" class="logo-ring"/>'
)

content = content.replace(
    '<path d="M10 12H14L18 24L22 12H26" stroke="url(#heroGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
    '<path d="M10 12H14L18 24L22 12H26" stroke="url(#heroGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="logo-icon"/>'
)

content = content.replace(
    '<circle cx="26" cy="24" r="2" fill="url(#heroGrad)"/>',
    '<circle cx="26" cy="24" r="2" fill="url(#heroGrad)" class="logo-dot"/>'
)

# Thêm logo-halo và đóng logo-container trước </svg>
content = content.replace(
    '</svg>',
    '<div class="logo-halo"></div>\n            </div>'
)

# Ghi file
with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("File đã được chỉnh sửa thành công!")
