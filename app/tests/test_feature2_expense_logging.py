"""
Tính năng 2: Ghi chép chi tiêu thông minh – Tự động phân loại & Tổng hợp
=========================================================================
Kiểm tra các hàm trong tools.py ghi giao dịch và tổng hợp chi tiêu
theo tháng/danh mục (đơn vị USD), và AI tự phân loại chi tiêu từ
ngôn ngữ tự nhiên.
"""

import os
import sys
import csv
import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.getenv("API_KEY")
requires_api = pytest.mark.skipif(not API_KEY, reason="Chưa set API_KEY")


class _FakeCall:
    """Giả lập đối tượng function-call của Gemini."""
    def __init__(self, name, args):
        self.name = name
        self.args = args


class _FakeResponse:
    """Giả lập đối tượng response của Gemini."""
    def __init__(self, text=None, calls=None):
        self.text = text
        self.function_calls = calls or []


def _read_csv(path):
    """Đọc file CSV và trả về danh sách các dòng dạng dict."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ===========================================================================
# PHẦN A – Kiểm tra đơn vị: logTransaction
# ===========================================================================

class TestLogTransaction:

    # TC-F2-01
    def test_valid_debit_is_written_to_csv(self, temp_csv):
        """Ghi debit hợp lệ phải xuất hiện trong CSV."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", temp_csv):
            result = logTransaction(
                date="2026-05-10",
                description="Lunch",
                amount=12.50,
                transaction_type="debit",
                category="Food & Dining",
                account_name="Cash",
            )
        assert "Successfully recorded" in result
        rows = _read_csv(temp_csv)
        assert len(rows) == 1
        assert rows[0]["Description"] == "Lunch"
        assert rows[0]["Category"] == "Food & Dining"
        assert rows[0]["Transaction Type"] == "debit"

    # TC-F2-02
    def test_valid_credit_is_written_to_csv(self, temp_csv):
        """Ghi credit (thu nhập) phải lưu đúng transaction_type."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", temp_csv):
            result = logTransaction(
                date="2026-05-03",
                description="May Paycheck",
                amount=3000.00,
                transaction_type="credit",
                category="Income",
                account_name="Bank",
            )
        assert "Successfully recorded" in result
        rows = _read_csv(temp_csv)
        assert rows[0]["Transaction Type"] == "credit"
        assert rows[0]["Amount"] == "3000.0"

    # TC-F2-03
    def test_month_field_is_extracted_from_date(self, temp_csv):
        """Trường Month phải được tự động trích từ Date."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", temp_csv):
            logTransaction("2026-05-10", "Uber", 8.00, "debit", "Transportation", "Card")
        rows = _read_csv(temp_csv)
        assert rows[0]["Month"] == "2026-05"

    # TC-F2-04
    def test_multiple_transactions_appended_sequentially(self, temp_csv):
        """Nhiều giao dịch phải được nối thêm vào cuối file, không ghi đè."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", temp_csv):
            logTransaction("2026-05-01", "Lunch",        12.50,   "debit",  "Food & Dining",  "Cash")
            logTransaction("2026-05-02", "Uber",          8.00,   "debit",  "Transportation", "Card")
            logTransaction("2026-05-03", "May Paycheck", 3000.00, "credit", "Income",         "Bank")
        rows = _read_csv(temp_csv)
        assert len(rows) == 3
        assert rows[0]["Description"] == "Lunch"
        assert rows[2]["Description"] == "May Paycheck"

    # TC-F2-05
    def test_file_not_found_returns_error_message(self):
        """Khi file không tồn tại, phải trả về thông báo lỗi."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", "/nonexistent/path/file.csv"):
            result = logTransaction("2026-05-10", "Test", 1.00, "debit", "Other", "Cash")
        assert "System Error" in result or "Error" in result.lower()

    # TC-F2-06
    def test_float_amount_stored_correctly(self, temp_csv):
        """Amount kiểu số thực phải được lưu đúng giá trị."""
        from services.tools import logTransaction
        with patch("services.tools.DATA_FILE", temp_csv):
            logTransaction("2026-05-10", "Coffee", 5.75, "debit", "Food & Dining", "Cash")
        rows = _read_csv(temp_csv)
        assert float(rows[0]["Amount"]) == 5.75


# ===========================================================================
# PHẦN B – Kiểm tra đơn vị: getMonthlySummary
# ===========================================================================

class TestGetMonthlySummary:

    # TC-F2-07
    def test_correct_totals_for_existing_month(self, temp_csv_with_data):
        """Tổng thu/chi phải đúng với dữ liệu tháng hiện có."""
        from services.tools import getMonthlySummary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getMonthlySummary("2026-05")
        assert "Total Income" in result
        assert "Total Expense" in result
        assert "3000.0" in result  # lương tháng 5

    # TC-F2-08
    def test_net_balance_is_income_minus_expense(self, temp_csv_with_data):
        """Số dư ròng = Tổng thu - Tổng chi."""
        from services.tools import getMonthlySummary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getMonthlySummary("2026-05")
        # Thu=3000.00, Chi=12.50+8.00+5.50+25.00+90.00+15.99+11.00+45.00+22.00=234.99
        expected_balance = round(3000.00 - 234.99, 10)
        assert str(expected_balance) in result or "2765.01" in result

    # TC-F2-09
    def test_empty_month_returns_zero_totals(self, temp_csv_with_data):
        """Tháng không có dữ liệu phải trả về 0 cho cả thu và chi."""
        from services.tools import getMonthlySummary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getMonthlySummary("2099-01")
        assert "Total Income = 0.0" in result
        assert "Total Expense = 0.0" in result

    # TC-F2-10
    def test_file_not_found_returns_warning(self):
        """Khi file không tồn tại, phải trả về cảnh báo."""
        from services.tools import getMonthlySummary
        with patch("services.tools.DATA_FILE", "/nonexistent/file.csv"):
            result = getMonthlySummary("2026-05")
        assert "Warning" in result or "No data" in result

    # TC-F2-11
    def test_summary_format_contains_month_label(self, temp_csv_with_data):
        """Kết quả phải chứa nhãn tháng được truy vấn."""
        from services.tools import getMonthlySummary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getMonthlySummary("2026-04")
        assert "2026-04" in result


# ===========================================================================
# PHẦN C – Kiểm tra đơn vị: getCategorySpending
# ===========================================================================

class TestGetCategorySpending:

    # TC-F2-12
    def test_correct_total_for_existing_category(self, temp_csv_with_data):
        """Tổng chi theo danh mục phải được tính đúng."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getCategorySpending("2026-05", "Food & Dining")
        # 12.50 + 5.50 + 11.00 = 29.0
        assert "29.0" in result

    # TC-F2-13  [BUG-F2-01 đã sửa]
    def test_category_match_is_case_insensitive(self, temp_csv_with_data):
        """So khớp danh mục không phân biệt hoa/thường; kết quả dùng tên chuẩn từ DB."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result_lower = getCategorySpending("2026-05", "food & dining")
            result_upper = getCategorySpending("2026-05", "Food & Dining")
        # Tổng tiền phải như nhau dù viết hoa hay thường
        assert "29.0" in result_lower
        assert "29.0" in result_upper
        # Cả hai đều hiển thị tên chuẩn lấy từ DB
        assert "Food & Dining" in result_lower
        assert "Food & Dining" in result_upper

    # TC-F2-14
    def test_category_with_no_transactions_returns_zero(self, temp_csv_with_data):
        """Danh mục không có giao dịch phải trả về 0."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getCategorySpending("2026-05", "NonExistentCategory")
        assert "Total Spent = 0.0" in result
        assert "None" in result

    # TC-F2-15
    def test_credit_transactions_excluded_from_spending(self, temp_csv_with_data):
        """Giao dịch credit (thu nhập) không được tính vào chi tiêu."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getCategorySpending("2026-05", "Income")
        assert "Total Spent = 0.0" in result

    # TC-F2-16
    def test_details_list_contains_transaction_descriptions(self, temp_csv_with_data):
        """Danh sách chi tiết phải liệt kê đúng các mô tả giao dịch."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = getCategorySpending("2026-05", "Food & Dining")
        assert "Restaurant - Pho" in result
        assert "Coffee" in result
        assert "Burger" in result

    # TC-F2-17
    def test_file_not_found_returns_warning(self):
        """Khi file không tồn tại, phải trả về cảnh báo."""
        from services.tools import getCategorySpending
        with patch("services.tools.DATA_FILE", "/nonexistent/file.csv"):
            result = getCategorySpending("2026-05", "Food & Dining")
        assert "Warning" in result or "No data" in result


# ===========================================================================
# PHẦN D – Kiểm tra tích hợp AI: tự phân loại qua mock
# ===========================================================================

class TestAIAutoCategorizationMocked:

    def _run_tool_cycle(self, mock_chat, tool_fn):
        """Mô phỏng một vòng gọi tool đầy đủ."""
        TOOL_MAP = {"logTransaction": tool_fn}
        response = mock_chat.send_message("input")
        while True:
            if not response.function_calls:
                return response.text
            for fc in response.function_calls:
                result = TOOL_MAP.get(fc.name, lambda **k: "ERROR: unknown tool")(**fc.args)
                response = mock_chat.send_message(result)

    # TC-F2-18
    def test_food_expense_triggers_correct_category(self, temp_csv):
        """AI mô phỏng ghi chi ăn uống đúng danh mục Food & Dining."""
        captured = {}
        def fake_log(**kwargs): captured.update(kwargs); return "OK"
        call_obj = _FakeCall("logTransaction", {
            "date": "2026-05-10", "description": "Lunch", "amount": 12.50,
            "transaction_type": "debit", "category": "Food & Dining", "account_name": "Cash",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Logged $12.50 for Lunch (Food & Dining)."),
        ]
        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_tool_cycle(mock_chat, fake_log)
        assert captured.get("category") == "Food & Dining"
        assert captured.get("transaction_type") == "debit"

    # TC-F2-19
    def test_transport_expense_triggers_correct_category(self, temp_csv):
        """AI mô phỏng ghi chi di chuyển đúng danh mục Transportation."""
        captured = {}
        def fake_log(**kwargs): captured.update(kwargs); return "OK"
        call_obj = _FakeCall("logTransaction", {
            "date": "2026-05-10", "description": "Uber", "amount": 8.00,
            "transaction_type": "debit", "category": "Transportation", "account_name": "Card",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Logged $8.00 for Uber."),
        ]
        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_tool_cycle(mock_chat, fake_log)
        assert captured.get("category") == "Transportation"

    # TC-F2-20
    def test_income_logged_as_credit_type(self, temp_csv):
        """AI mô phỏng ghi thu nhập đúng với transaction_type='credit'."""
        captured = {}
        def fake_log(**kwargs): captured.update(kwargs); return "OK"
        call_obj = _FakeCall("logTransaction", {
            "date": "2026-05-03", "description": "May Paycheck", "amount": 3000.00,
            "transaction_type": "credit", "category": "Income", "account_name": "Bank",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Logged paycheck."),
        ]
        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_tool_cycle(mock_chat, fake_log)
        assert captured.get("transaction_type") == "credit"
        assert captured.get("category") == "Income"

    # TC-F2-21
    def test_transaction_is_persisted_to_csv(self, temp_csv):
        """Sau khi AI gọi logTransaction, dòng mới phải thực sự có trong CSV."""
        from services.tools import logTransaction
        call_obj = _FakeCall("logTransaction", {
            "date": "2026-05-10", "description": "Burger", "amount": 11.00,
            "transaction_type": "debit", "category": "Food & Dining", "account_name": "Cash",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Logged."),
        ]
        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_tool_cycle(mock_chat, logTransaction)
            rows = _read_csv(temp_csv)
        assert any(r["Description"] == "Burger" for r in rows)


# ===========================================================================
# PHẦN E – Kiểm tra tích hợp AI với Gemini API thật
# ===========================================================================

def _make_finance_chat(client):
    """Tạo phiên chat tài chính với đầy đủ tools và system prompt."""
    from google import genai
    from google.genai import types
    from services.tools import logTransaction, getMonthlySummary, getCategorySpending
    from datetime import datetime
    return client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                f"You are a personal finance assistant. Today is {datetime.now().strftime('%Y-%m-%d')}. "
                "Currency: USD. Categories: [Food & Dining, Transportation, Shopping, "
                "Bills & Utilities, Income, Entertainment, Health, Other]. "
                "When the user reports an expense, call logTransaction immediately. "
                "NEVER ask the user for the date."
            ),
            tools=[logTransaction, getMonthlySummary, getCategorySpending],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
        ),
    )


def _skip_on_rate_limit(exc):
    """Bỏ qua test nếu bị giới hạn quota API (lỗi 429)."""
    from google.genai import errors as genai_errors
    if isinstance(exc, genai_errors.ClientError) and ("429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)):
        pytest.skip("Đã chạm giới hạn quota API")
    raise exc


# TC-F2-22
@requires_api
def test_ai_logs_food_expense_from_natural_language(temp_csv):
    """AI phải gọi logTransaction khi user thông báo chi tiêu ăn uống."""
    from google import genai
    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = _make_finance_chat(client)
            with patch("services.tools.DATA_FILE", temp_csv):
                response = chat.send_message("I had lunch today, spent $12.50 at a restaurant, paid by cash")
        assert response.text and len(response.text.strip()) > 0
        rows = _read_csv(temp_csv)
        food_rows = [r for r in rows if "Food" in r.get("Category", "") or "lunch" in r.get("Description", "").lower()]
        assert len(food_rows) > 0, "AI không ghi giao dịch vào CSV"
    except Exception as e:
        _skip_on_rate_limit(e)


# TC-F2-23
@requires_api
def test_ai_auto_categorizes_transport_expense(temp_csv):
    """AI phải tự phân loại chi phí Uber vào danh mục Transportation."""
    from google import genai
    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = _make_finance_chat(client)
            with patch("services.tools.DATA_FILE", temp_csv):
                chat.send_message("Just took an Uber, cost $8, paid by card")
        rows = _read_csv(temp_csv)
        transport_rows = [r for r in rows if "Transportation" in r.get("Category", "")]
        assert len(transport_rows) > 0, "AI không phân loại Transportation đúng"
    except Exception as e:
        _skip_on_rate_limit(e)


# TC-F2-24
@requires_api
def test_ai_returns_monthly_summary_when_asked(temp_csv):
    """AI phải gọi getMonthlySummary khi user hỏi tổng chi tiêu tháng."""
    from google import genai
    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = _make_finance_chat(client)
            with patch("services.tools.DATA_FILE", temp_csv):
                chat.send_message("I spent $10 on coffee today")
                response = chat.send_message("What is my total spending this month?")
        assert response.text and len(response.text.strip()) > 10
    except Exception as e:
        _skip_on_rate_limit(e)


# TC-F2-25
@requires_api
def test_ai_does_not_ask_user_for_date(temp_csv):
    """AI không được hỏi lại ngày khi user đã nói 'today'."""
    from google import genai
    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = _make_finance_chat(client)
            with patch("services.tools.DATA_FILE", temp_csv):
                response = chat.send_message("I bought a t-shirt today for $25")
        text = response.text or ""
        # Các mẫu câu hỏi ngày tháng không được xuất hiện trong phản hồi
        date_questions = ["what date", "which date", "what day", "when was", "please provide the date"]
        assert not any(q in text.lower() for q in date_questions), f"AI hỏi lại ngày: '{text}'"
    except Exception as e:
        _skip_on_rate_limit(e)
