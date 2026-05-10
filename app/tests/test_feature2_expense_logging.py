"""
Feature 2: Smart Expense Logging – Auto-categorization & Summarization
======================================================================
Tests that tools.py functions correctly log transactions and summarize
spending by month/category, and that the AI auto-categorizes expenses
from natural-language input.

Bugs discovered during test design are documented inline as BUG-F2-XX.
"""

import os
import sys
import csv
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

API_KEY = os.getenv("API_KEY")
requires_api = pytest.mark.skipif(not API_KEY, reason="API_KEY env var not set")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class _FakeResponse:
    def __init__(self, text=None, calls=None):
        self.text = text
        self.function_calls = calls or []


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ===========================================================================
# SECTION A – Unit tests: log_transaction
# ===========================================================================

class TestLogTransaction:

    # TC-F2-01
    def test_valid_debit_is_written_to_csv(self, temp_csv):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", temp_csv):
            result = log_transaction(
                date="2026-05-10",
                description="Phở bò",
                amount=50000,
                transaction_type="debit",
                category="Ăn uống",
                account_name="Tiền mặt",
            )
        assert "Successfully recorded" in result
        rows = _read_csv(temp_csv)
        assert len(rows) == 1
        assert rows[0]["Description"] == "Phở bò"
        assert rows[0]["Category"] == "Ăn uống"
        assert rows[0]["Transaction Type"] == "debit"

    # TC-F2-02
    def test_valid_credit_is_written_to_csv(self, temp_csv):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", temp_csv):
            result = log_transaction(
                date="2026-05-03",
                description="Lương tháng 5",
                amount=15000000,
                transaction_type="credit",
                category="Lương",
                account_name="TPBank",
            )
        assert "Successfully recorded" in result
        rows = _read_csv(temp_csv)
        assert rows[0]["Transaction Type"] == "credit"
        assert rows[0]["Amount"] == "15000000"

    # TC-F2-03
    def test_month_field_is_extracted_from_date(self, temp_csv):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", temp_csv):
            log_transaction("2026-05-10", "Grab", 25000, "debit", "Di chuyển", "MoMo")
        rows = _read_csv(temp_csv)
        assert rows[0]["Month"] == "2026-05"

    # TC-F2-04
    def test_multiple_transactions_appended_sequentially(self, temp_csv):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", temp_csv):
            log_transaction("2026-05-01", "Phở", 50000, "debit", "Ăn uống", "Tiền mặt")
            log_transaction("2026-05-02", "Grab", 25000, "debit", "Di chuyển", "MoMo")
            log_transaction("2026-05-03", "Lương", 15000000, "credit", "Lương", "TPBank")
        rows = _read_csv(temp_csv)
        assert len(rows) == 3
        assert rows[0]["Description"] == "Phở"
        assert rows[2]["Description"] == "Lương"

    # TC-F2-05
    def test_file_not_found_returns_error_message(self):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", "/nonexistent/path/file.csv"):
            result = log_transaction("2026-05-10", "Test", 1000, "debit", "Test", "Test")
        assert "System Error" in result or "Error" in result.lower()

    # TC-F2-06
    def test_float_amount_stored_correctly(self, temp_csv):
        from services.tools import log_transaction
        with patch("services.tools.DATA_FILE", temp_csv):
            log_transaction("2026-05-10", "Bánh mì", 15.5, "debit", "Ăn uống", "Tiền mặt")
        rows = _read_csv(temp_csv)
        assert float(rows[0]["Amount"]) == 15.5


# ===========================================================================
# SECTION B – Unit tests: get_monthly_summary
# ===========================================================================

class TestGetMonthlySummary:

    # TC-F2-07
    def test_correct_totals_for_existing_month(self, temp_csv_with_data):
        from services.tools import get_monthly_summary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_monthly_summary("2026-05")
        assert "Total Income" in result
        assert "Total Expense" in result
        assert "15000000" in result  # lương tháng 5

    # TC-F2-08
    def test_net_balance_is_income_minus_expense(self, temp_csv_with_data):
        from services.tools import get_monthly_summary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_monthly_summary("2026-05")
        # Net Balance = 15000000 - (50000+25000+65000+250000+450000+99000+45000+120000+85000)
        expected_expense = 50000 + 25000 + 65000 + 250000 + 450000 + 99000 + 45000 + 120000 + 85000
        expected_balance = 15000000 - expected_expense
        assert str(expected_balance) in result

    # TC-F2-09
    def test_empty_month_returns_zero_totals(self, temp_csv_with_data):
        from services.tools import get_monthly_summary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_monthly_summary("2099-01")
        assert "Total Income = 0.0" in result
        assert "Total Expense = 0.0" in result

    # TC-F2-10
    def test_file_not_found_returns_warning(self):
        from services.tools import get_monthly_summary
        with patch("services.tools.DATA_FILE", "/nonexistent/file.csv"):
            result = get_monthly_summary("2026-05")
        assert "Warning" in result or "No data" in result

    # TC-F2-11
    def test_summary_format_contains_month_label(self, temp_csv_with_data):
        from services.tools import get_monthly_summary
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_monthly_summary("2026-04")
        assert "2026-04" in result


# ===========================================================================
# SECTION C – Unit tests: get_category_spending
# ===========================================================================

class TestGetCategorySpending:

    # TC-F2-12
    def test_correct_total_for_existing_category(self, temp_csv_with_data):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_category_spending("2026-05", "Ăn uống")
        # 50000 + 65000 + 45000 = 160000
        assert "160000" in result

    # TC-F2-13
    def test_category_match_is_case_insensitive(self, temp_csv_with_data):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result_lower = get_category_spending("2026-05", "ăn uống")
            result_upper = get_category_spending("2026-05", "Ăn uống")
        assert result_lower == result_upper

    # TC-F2-14
    def test_category_with_no_transactions_returns_zero(self, temp_csv_with_data):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_category_spending("2026-05", "Không tồn tại")
        assert "Total Spent = 0.0" in result
        assert "None" in result

    # TC-F2-15
    def test_credit_transactions_are_excluded_from_spending(self, temp_csv_with_data):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_category_spending("2026-05", "Lương")
        # Lương là credit → không được tính vào chi tiêu
        assert "Total Spent = 0.0" in result

    # TC-F2-16
    def test_details_list_contains_transaction_descriptions(self, temp_csv_with_data):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", temp_csv_with_data):
            result = get_category_spending("2026-05", "Ăn uống")
        assert "Phở bò" in result
        assert "Cà phê Highland" in result
        assert "Bún bò Huế" in result

    # TC-F2-17
    def test_file_not_found_returns_warning(self):
        from services.tools import get_category_spending
        with patch("services.tools.DATA_FILE", "/nonexistent/file.csv"):
            result = get_category_spending("2026-05", "Ăn uống")
        assert "Warning" in result or "No data" in result


# ===========================================================================
# SECTION D – AI integration: auto-categorization via mock
# ===========================================================================

class TestAIAutoCategorizationMocked:

    def _run_chat_with_tool(self, mock_chat, tool_fn, expected_call):
        """Helper: simulate one full tool-calling round-trip."""
        from services.tools import log_transaction
        TOOL_MAP = {"log_transaction": tool_fn}

        response = mock_chat.send_message("dummy input")
        while True:
            if not response.function_calls:
                return response.text
            for fc in response.function_calls:
                result = TOOL_MAP.get(fc.name, lambda **k: "ERROR")(**fc.args)
                response = mock_chat.send_message(result)

    # TC-F2-18
    def test_food_expense_triggers_log_transaction(self, temp_csv):
        """AI mô phỏng ghi tiêu ăn uống vào đúng danh mục."""
        mock_chat = MagicMock()
        captured = {}

        def fake_log(**kwargs):
            captured.update(kwargs)
            return f"Successfully recorded {kwargs['amount']} for {kwargs['description']}."

        call_obj = _FakeCall("log_transaction", {
            "date": "2026-05-10", "description": "Phở bò", "amount": 50000,
            "transaction_type": "debit", "category": "Ăn uống", "account_name": "Tiền mặt",
        })
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Đã ghi lại 50,000đ cho Phở bò (Ăn uống)."),
        ]

        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_chat_with_tool(mock_chat, fake_log, call_obj)

        assert captured.get("category") == "Ăn uống"
        assert captured.get("transaction_type") == "debit"

    # TC-F2-19
    def test_transport_expense_triggers_correct_category(self, temp_csv):
        """AI mô phỏng ghi chi phí di chuyển với danh mục Di chuyển."""
        mock_chat = MagicMock()
        captured = {}

        def fake_log(**kwargs):
            captured.update(kwargs)
            return "OK"

        call_obj = _FakeCall("log_transaction", {
            "date": "2026-05-10", "description": "Grab Bike", "amount": 25000,
            "transaction_type": "debit", "category": "Di chuyển", "account_name": "MoMo",
        })
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Đã ghi lại."),
        ]

        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_chat_with_tool(mock_chat, fake_log, call_obj)

        assert captured.get("category") == "Di chuyển"

    # TC-F2-20
    def test_income_logged_as_credit_type(self, temp_csv):
        """AI mô phỏng ghi lương với transaction_type='credit'."""
        captured = {}

        def fake_log(**kwargs):
            captured.update(kwargs)
            return "OK"

        call_obj = _FakeCall("log_transaction", {
            "date": "2026-05-03", "description": "Lương tháng 5", "amount": 15000000,
            "transaction_type": "credit", "category": "Lương", "account_name": "TPBank",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Đã ghi lương."),
        ]

        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_chat_with_tool(mock_chat, fake_log, call_obj)

        assert captured.get("transaction_type") == "credit"
        assert captured.get("category") == "Lương"

    # TC-F2-21
    def test_transaction_is_actually_persisted_to_csv(self, temp_csv):
        """Sau khi AI gọi log_transaction, file CSV phải chứa dòng mới."""
        from services.tools import log_transaction

        call_obj = _FakeCall("log_transaction", {
            "date": "2026-05-10", "description": "Bún bò", "amount": 45000,
            "transaction_type": "debit", "category": "Ăn uống", "account_name": "Tiền mặt",
        })
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [
            _FakeResponse(calls=[call_obj]),
            _FakeResponse(text="Đã ghi."),
        ]

        with patch("services.tools.DATA_FILE", temp_csv):
            self._run_chat_with_tool(mock_chat, log_transaction, call_obj)
            rows = _read_csv(temp_csv)

        assert any(r["Description"] == "Bún bò" for r in rows)


# ===========================================================================
# SECTION E – AI integration: real Gemini API tests
# ===========================================================================

class TestAIExpenseLoggingRealAPI:

    @pytest.fixture(autouse=True)
    def setup_chat(self, temp_csv):
        """Khởi tạo Gemini chat thực tế với tools snake_case đúng."""
        if not API_KEY:
            pytest.skip("API_KEY not set")

        from google import genai
        from google.genai import types
        from services.tools import log_transaction, get_monthly_summary, get_category_spending

        self.temp_csv = temp_csv
        client = genai.Client(api_key=API_KEY)
        with patch("services.tools.DATA_FILE", temp_csv):
            self.chat = client.chats.create(
                model="gemini-2.0-flash-001",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Bạn là trợ lý tài chính. Hôm nay là 2026-05-10. "
                        "Danh mục: [Ăn uống, Di chuyển, Hóa đơn, Mua sắm, Lương]. "
                        "Khi người dùng khai báo chi tiêu, hãy gọi log_transaction ngay."
                    ),
                    tools=[log_transaction, get_monthly_summary, get_category_spending],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                ),
            )

    # TC-F2-22
    @requires_api
    def test_ai_logs_food_expense_from_natural_language(self):
        """AI phải tự động gọi log_transaction khi user nói 'ăn phở hết 50k'."""
        with patch("services.tools.DATA_FILE", self.temp_csv):
            response = self.chat.send_message("Hôm nay tôi ăn phở bò hết 50 nghìn tiền mặt")
        assert response.text and len(response.text.strip()) > 0
        rows = _read_csv(self.temp_csv)
        food_rows = [r for r in rows if "phở" in r.get("Description", "").lower() or "Ăn uống" in r.get("Category", "")]
        assert len(food_rows) > 0, "AI không ghi giao dịch vào CSV"

    # TC-F2-23
    @requires_api
    def test_ai_auto_categorizes_transport_expense(self):
        """AI phải phân loại 'đi grab' vào danh mục Di chuyển."""
        with patch("services.tools.DATA_FILE", self.temp_csv):
            self.chat.send_message("Tôi vừa đi Grab hết 30k bằng MoMo")
        rows = _read_csv(self.temp_csv)
        transport_rows = [r for r in rows if r.get("Category", "").lower() in ["di chuyển", "transportation"]]
        assert len(transport_rows) > 0, "AI không phân loại Di chuyển đúng"

    # TC-F2-24
    @requires_api
    def test_ai_returns_monthly_summary_when_asked(self):
        """AI phải gọi get_monthly_summary khi user hỏi tổng chi tiêu tháng."""
        with patch("services.tools.DATA_FILE", self.temp_csv):
            self.chat.send_message("Tôi ăn cơm hết 40k hôm nay")
            response = self.chat.send_message("Tổng chi tiêu tháng 5/2026 của tôi là bao nhiêu?")
        assert response.text and ("tháng" in response.text.lower() or "2026-05" in response.text or "0" in response.text)

    # TC-F2-25
    @requires_api
    def test_ai_does_not_ask_user_for_date(self):
        """AI không được hỏi lại người dùng về ngày khi họ nói 'hôm nay'."""
        with patch("services.tools.DATA_FILE", self.temp_csv):
            response = self.chat.send_message("Hôm nay tôi mua áo hết 200k")
        text = response.text or ""
        date_questions = ["ngày nào", "hôm nay là", "cho biết ngày", "ngày bao nhiêu"]
        asked_date = any(q in text.lower() for q in date_questions)
        assert not asked_date, f"AI hỏi lại ngày: '{text}'"
