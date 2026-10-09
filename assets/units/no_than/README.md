# Nỏ Thần – bộ asset tháp (bản thử nghiệm)

Tháp bắn tên lấy cảm hứng từ nỏ thần Cổ Loa của An Dương Vương.
Toàn bộ được sinh bằng `tools/gen_no_than.py` (pixel art vẽ thủ tục), chạy lại script để tái tạo.

## Cấp độ

| Cấp | Tên | Đặc điểm hình ảnh |
|---|---|---|
| 1 | Nỏ Cổ Loa | Đế đất nện (thấy rõ các lớp đất như thành Cổ Loa), rào cọc gỗ, nỏ gỗ, lẫy gỗ |
| 2 | Nỏ Đồng | Đế đá, lan can gỗ, cờ đỏ, cánh nỏ và đai bằng đồng, lẫy đồng |
| 3 | Nỏ Thần Liên Châu | Đế đá có đai hoa văn trống đồng Đông Sơn, mặt trời trống đồng trên sàn, cột son, 2 cờ, cánh nỏ vàng phát sáng, lẫy **vuốt Rùa Vàng**, nạp 3 mũi tên |

## File

| File | Khung | Số frame | Ghi chú |
|---|---|---|---|
| `sprites/tower_lv{1,2,3}_idle.png` | 64×64 | 4 | lặp; cờ / ruy băng bay, lv3 hào quang nhấp nháy |
| `sprites/tower_lv{1,2,3}_attack.png` | 64×64 | 6 | sẵn sàng → căng dây → **nhả (frame 2, sinh đạn)** → giật → quay tời → lắp tên |
| `sprites/projectile_arrow.png` | 16×8 | 4 | tên mũi đồng (mũi tên đồng Cổ Loa), xoay theo hướng bay |
| `sprites/projectile_divine.png` | 24×12 | 4 | thần tiễn vàng có vệt sáng (lv3) |
| `sprites/fx_hit.png`, `fx_hit_divine.png` | 32×32 | 6 | hiệu ứng trúng đích |
| `ui/icon_build.png` | 32×32 | 1 | icon xây tháp |
| `ui/icon_skill_than_tien.png` | 32×32 | 1 | icon kỹ năng "Thần Tiễn Liên Châu" |
| `no_than.json` | | | metadata: anchor, thời lượng frame, điểm sinh đạn, frame bắn |
| `preview/` | | | GIF phóng to 4–6× và `contact_sheet.png` để xem nhanh |

Sprite sheet là dải ngang, nền trong suốt. Anchor của tháp là `(32, 57)` (tâm chân đế).
Nỏ vẽ quay sang phải; lật ngang để quay trái.

## Giới hạn hiện tại

- Nỏ chỉ có hướng phải/trái (lật), chưa có 8 hướng xoay.
- Chưa có frame xây dựng / phá huỷ, chưa có âm thanh.
