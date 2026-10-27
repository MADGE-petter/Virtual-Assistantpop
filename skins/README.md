# Thư mục Skins Tùy Chỉnh cho Mascot (Custom Skins)

Bạn có thể tự thêm bất kỳ nhân vật yêu thích, meme hoặc anime nào (như Doro, Phoebe, Noa, Hsin, Transformers, Băng thần Mixue...) vào đây. Ứng dụng sẽ tự động quét thư mục này và thêm nhân vật vào **Giao diện Bộ Sưu Tập & Gacha**!

---

## Cấu trúc một gói skin:

Mỗi nhân vật là một thư mục con nằm trong `skins/`:

```
skins/
  └── my_favorite_character/
        ├── manifest.json       (bắt buộc)
        ├── idle.png            (bắt buộc - trạng thái bình thường)
        ├── blink.png           (tuỳ chọn - chớp mắt)
        ├── talk.png            (tuỳ chọn - khi đang nói chuyện)
        └── sleep.png           (tuỳ chọn - khi mascot đi ngủ)
```

---

## File `manifest.json` mẫu:

```json
{
  "id": "my_favorite_character",
  "name": "Tên Nhân Vật Của Bạn",
  "rarity": "epic",
  "price": 4000,
  "description": "Mô tả ngắn gọn về nhân vật này.",
  "in_gacha": true
}
```

### Các cấp độ hiếm (`rarity`):
* `common` - Thường (Màu xám, giá mặc định 500 coin)
* `rare` - Hiếm (Màu xanh dương, giá mặc định 1.500 coin)
* `epic` - Sử thi (Màu tím, giá mặc định 4.000 coin)
* `legendary` - Huyền thoại (Màu vàng cam, giá mặc định 10.000 coin)
* `mythic` - Thần thoại (Màu đỏ hồng, giá mặc định 20.000 coin)

---

## Yêu cầu hình ảnh:
- Định dạng: `.png` với nền trong suốt (transparent).
- Kích thước khuyến nghị: `128x128` pixel hoặc `256x256` pixel.
- Nếu không có file `blink.png`, `talk.png` hay `sleep.png`, hệ thống sẽ tự động dùng ảnh `idle.png`.
