# Sơ đồ luồng hoạt động Crawler (AWS Lambda)

**Trigger:** `AWS Lambda Trigger` (Cronjob / EventBridge)

---

## Pha 1: Khởi tạo & Đồng bộ trạng thái

- Tải file từ S3 xuống thư mục `/tmp/article_urls.json`.
- _(Nếu chưa có trên S3 thì hệ thống sẽ tự tạo một file rỗng)._

---

## Pha 2: Crawl Index (Tìm bài viết mới)

- Truy cập trang danh sách (`album.html`).
- Lấy các URL mới và đưa vào danh sách với trạng thái là `"not_crawled"`.
- **[Tối ưu] EARLY EXIT:** Nếu phát hiện trang hiện tại toàn bộ là bài viết cũ -> **DỪNG** phân trang ngay lập tức (bỏ qua việc cào các trang tiếp theo).
- Lưu nháp file JSON cục bộ và upload tạm lên S3.

---

## Pha 3: Batch Check (Lọc trùng với Database)

- Lọc ra các URL đang có trạng thái `"not_crawled"` và `"failed"`.
- Gọi API `POST /api/v1/ceo-interviews/check-bulk` để truyền một lần toàn bộ danh sách URL sang FastAPI.
- FastAPI sử dụng toán tử `$in` query Database để kiểm tra cực nhanh và trả về danh sách các URL đã tồn tại.
- Lambda cập nhật trạng thái của các URL trùng lặp này thành `"crawled"`.
  > **Kết quả:** Ở bước tiếp theo, hệ thống chỉ còn giữ lại những URL THỰC SỰ MỚI.

---

## Pha 4: Crawl Article (Xử lý dữ liệu chi tiết)

**Tiến hành lặp qua từng URL mới:**

1. **[Tối ưu] TIME-BOXING:** Kiểm tra thời gian sống bằng `context.get_remaining_time_in_millis()`. Nếu thời gian còn lại dưới 30 giây -> **BREAK** (Thoát vòng lặp ngay lập tức).
2. **[Tối ưu] CIRCUIT BREAKER (Ngắt cầu dao):** Nếu gặp lỗi Timeout mạng (sau 10s) liên tiếp từ 5 lần trở lên -> **BREAK** (Đề phòng trường hợp IP bị block hoặc WAF chặn).
3. Cào HTML nội dung chi tiết của bài viết.
4. Gọi API `POST /api/v1/ceo-interviews/` để lưu vào Database:
   - Lưu thành công -> Chuyển trạng thái thành `"crawled"`.
   - Lưu thất bại -> Chuyển trạng thái thành `"failed"`.
5. **[Tối ưu] DELAY:** Tạm nghỉ 1.5 giây giữa mỗi bài để chống rate-limit từ máy chủ mục tiêu.

---

## Pha 5: Lưu trữ trạng thái (Teardown)

- **[Tối ưu]** Ghi đè cập nhật vào file `/tmp/article_urls.json` **MỘT LẦN DUY NHẤT** ở cuối vòng lặp (Giúp giảm tải I/O cho ổ cứng).
- Upload file JSON lên S3 (Ghi đè lên phiên bản cũ).
- Trả về status `200 OK` - Kết thúc tiến trình Lambda một cách an toàn.
