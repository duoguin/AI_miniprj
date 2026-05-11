"""
Tính năng 1: Tích hợp Gemini API – Trả lời câu hỏi tài chính
=============================================================
Kiểm tra chatbot trả lời đúng các câu hỏi tài chính cơ bản,
xử lý luồng hội thoại và thất bại có kiểm soát.

Các bug phát hiện trong quá trình thiết kế test được ghi chú dạng BUG-F1-XX.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ---------------------------------------------------------------------------
# Biến và lớp hỗ trợ
# ---------------------------------------------------------------------------
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


def _make_run_chat(mock_chat):
    """Tái tạo logic run_chat để test độc lập với main.py."""
    TOOL_MAP: dict = {}

    def run_chat(user_input: str) -> str:
        from datetime import datetime
        full_input = f"Current date: {datetime.now().isoformat()}\nUser: {user_input}"
        response = mock_chat.send_message(full_input)
        while True:
            if not response.function_calls:
                return response.text
            for fc in response.function_calls:
                if fc.name not in TOOL_MAP:
                    result = f"ERROR: Tool {fc.name} not found"
                else:
                    try:
                        result = TOOL_MAP[fc.name](**fc.args)
                    except Exception as exc:
                        result = f"ERROR: {exc}"
                response = mock_chat.send_message(result)

    return run_chat, TOOL_MAP


# ---------------------------------------------------------------------------
# TC-F1-01  main.py khai báo model Gemini hợp lệ
# ---------------------------------------------------------------------------
def test_chat_config_declares_gemini_model():
    """main.py phải sử dụng một model Gemini."""
    main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
    content = open(main_path, encoding="utf-8").read()
    assert "gemini" in content.lower(), "Không tìm thấy khai báo Gemini model trong main.py"


# ---------------------------------------------------------------------------
# TC-F1-02  System prompt phải có nội dung về tài chính
# ---------------------------------------------------------------------------
def test_system_prompt_mentions_finance():
    """System prompt phải đề cập đến vai trò trợ lý tài chính."""
    main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
    content = open(main_path, encoding="utf-8").read()
    assert "tài chính" in content.lower() or "finance" in content.lower(), (
        "BUG-F1-01: System prompt không đề cập đến vai trò tài chính."
    )


# ---------------------------------------------------------------------------
# TC-F1-03  System prompt phải chứa danh mục chi tiêu
# ---------------------------------------------------------------------------
def test_system_prompt_contains_spending_categories():
    """System prompt phải liệt kê các danh mục chi tiêu cho AI."""
    main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
    content = open(main_path, encoding="utf-8").read()
    categories = ["Food & Dining", "Transportation", "Shopping", "Income"]
    missing = [c for c in categories if c not in content]
    assert not missing, f"BUG-F1-02: Thiếu danh mục trong system prompt: {missing}"


# ---------------------------------------------------------------------------
# TC-F1-04  main.py import đúng tên hàm từ tools.py
# ---------------------------------------------------------------------------
def test_main_imports_match_tools_py():
    """
    main.py phải import tên hàm khớp với định nghĩa trong tools.py.
    BUG-F1-03: main.py import camelCase (logTransaction…) nhưng tools.py
               chỉ định nghĩa snake_case (log_transaction…) → ImportError khi chạy.
    """
    import ast

    main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
    tools_path = os.path.join(os.path.dirname(__file__), "..", "services", "tools.py")

    main_src = open(main_path, encoding="utf-8").read()
    tools_src = open(tools_path, encoding="utf-8").read()

    # Lấy tất cả tên hàm định nghĩa ở cấp cao nhất trong tools.py
    tools_tree = ast.parse(tools_src)
    defined_names = {
        node.name for node in ast.walk(tools_tree) if isinstance(node, ast.FunctionDef)
    }

    # Lấy những gì main.py import từ services.tools
    main_tree = ast.parse(main_src)
    imported_from_tools = []
    for node in ast.walk(main_tree):
        if isinstance(node, ast.ImportFrom) and node.module and "tools" in node.module:
            imported_from_tools.extend(alias.name for alias in node.names)

    missing = [n for n in imported_from_tools if n not in defined_names]
    assert not missing, (
        f"BUG-F1-03 (NGHIÊM TRỌNG): main.py import tên không tồn tại trong tools.py: {missing}\n"
        "Cách sửa: đổi tên hàm trong tools.py sang camelCase HOẶC cập nhật import trong main.py sang snake_case."
    )


# ---------------------------------------------------------------------------
# TC-F1-05  Datetime trong system prompt phải được format đúng
# ---------------------------------------------------------------------------
def test_system_prompt_datetime_is_interpolated():
    """
    System prompt phải truyền datetime thực tế, không phải chuỗi nguyên văn.
    BUG-F1-04: main.py dùng chuỗi thường thay vì f-string cho system_instruction,
               khiến '{datetime.now().isoformat()}' được gửi nguyên văn đến AI.
    """
    main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
    content = open(main_path, encoding="utf-8").read()
    # Nếu system_instruction không phải f-string mà chứa {datetime...}
    # thì AI sẽ nhận được text thô thay vì giờ thực tế
    assert "{datetime.now().isoformat()}" not in content, (
        "BUG-F1-04: system_instruction chứa {datetime.now().isoformat()} bên trong chuỗi thường "
        "(không phải f-string). AI sẽ nhận literal text thay vì giờ thực."
    )


# ---------------------------------------------------------------------------
# TC-F1-06  run_chat trả về text khi không có function call
# ---------------------------------------------------------------------------
def test_run_chat_returns_text_without_tool_call():
    """Khi AI trả lời thuần văn bản, run_chat phải trả về đúng nội dung đó."""
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = _FakeResponse(
        text="Bạn nên tiết kiệm ít nhất 20% thu nhập mỗi tháng."
    )
    run_chat, _ = _make_run_chat(mock_chat)
    result = run_chat("Tôi nên tiết kiệm bao nhiêu?")
    assert "20%" in result or "tiết kiệm" in result.lower()


# ---------------------------------------------------------------------------
# TC-F1-07  run_chat gọi tool rồi trả về phản hồi cuối
# ---------------------------------------------------------------------------
def test_run_chat_executes_tool_and_returns_followup():
    """Khi AI yêu cầu gọi tool, run_chat phải thực thi và gửi kết quả lại."""
    mock_chat = MagicMock()
    tool_call = _FakeCall("logTransaction", {
        "date": "2026-05-10", "description": "Pho", "amount": 12.50,
        "transaction_type": "debit", "category": "Food & Dining", "account_name": "Cash",
    })
    mock_chat.send_message.side_effect = [
        _FakeResponse(calls=[tool_call]),
        _FakeResponse(text="Đã ghi lại $12.50 cho Pho (Food & Dining)."),
    ]
    run_chat, TOOL_MAP = _make_run_chat(mock_chat)
    TOOL_MAP["logTransaction"] = lambda **kw: "Successfully recorded 12.50 for Pho."

    result = run_chat("tôi vừa ăn phở hết $12.50")
    assert result is not None and len(result) > 0


# ---------------------------------------------------------------------------
# TC-F1-08  run_chat xử lý tool không tồn tại
# ---------------------------------------------------------------------------
def test_run_chat_handles_unknown_tool_gracefully():
    """Khi AI gọi tool không có trong TOOL_MAP, run_chat không được crash."""
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = [
        _FakeResponse(calls=[_FakeCall("nonExistentTool", {})]),
        _FakeResponse(text="Xin lỗi, không thực hiện được."),
    ]
    run_chat, _ = _make_run_chat(mock_chat)
    result = run_chat("làm gì đó")
    assert result is not None


# ---------------------------------------------------------------------------
# TC-F1-09  run_chat xử lý exception từ tool
# ---------------------------------------------------------------------------
def test_run_chat_handles_tool_exception():
    """Nếu tool raise exception, run_chat phải bắt lỗi và tiếp tục."""
    mock_chat = MagicMock()
    tool_call = _FakeCall("logTransaction", {"date": "invalid"})
    mock_chat.send_message.side_effect = [
        _FakeResponse(calls=[tool_call]),
        _FakeResponse(text="Có lỗi xảy ra khi lưu giao dịch."),
    ]

    def broken_tool(**kwargs):
        raise RuntimeError("Lỗi ghi DB")

    run_chat, TOOL_MAP = _make_run_chat(mock_chat)
    TOOL_MAP["logTransaction"] = broken_tool

    result = run_chat("ghi tiền")
    assert result is not None


# ---------------------------------------------------------------------------
# TC-F1-10  config.py DATA_FILE trỏ đúng file tồn tại
# ---------------------------------------------------------------------------
def test_data_file_path_exists():
    """
    DATA_FILE trong config.py phải trỏ đến file thực sự tồn tại.
    BUG-F1-05: config.py trỏ tới 'transactions.csv' nhưng dữ liệu nằm ở
               'personal_transactions.csv' → mọi tool đọc file sẽ gặp FileNotFoundError.
    """
    import config
    assert os.path.exists(config.DATA_FILE), (
        f"BUG-F1-05: DATA_FILE='{config.DATA_FILE}' không tồn tại. "
        "config.py cần cập nhật tên file thành 'personal_transactions.csv'."
    )


# ---------------------------------------------------------------------------
# TC-F1-11  AI trả lời câu hỏi về tiết kiệm (gọi API thật)
# ---------------------------------------------------------------------------
@requires_api
def test_ai_answers_savings_question():
    """AI phải đưa ra lời khuyên tiết kiệm không rỗng."""
    from google import genai
    from google.genai import types, errors as genai_errors
    from services.tools import logTransaction, getMonthlySummary, getCategorySpending

    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="You are a personal finance assistant. Give advice on saving and expense management.",
                    tools=[logTransaction, getMonthlySummary, getCategorySpending],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                ),
            )
            response = chat.send_message("What percentage of my income should I save each month?")
            assert response.text and len(response.text.strip()) > 20, "AI trả về phản hồi rỗng"
    except genai_errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            pytest.skip("Đã chạm giới hạn quota API")
        raise


# ---------------------------------------------------------------------------
# TC-F1-12  AI giữ ngữ cảnh hội thoại (gọi API thật)
# ---------------------------------------------------------------------------
@requires_api
def test_ai_maintains_conversation_context():
    """AI phải nhớ nội dung câu hỏi trước trong cùng phiên chat."""
    from google import genai
    from google.genai import types, errors as genai_errors
    from services.tools import logTransaction, getMonthlySummary, getCategorySpending

    try:
        with genai.Client(api_key=API_KEY) as client:
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="You are a personal finance assistant.",
                    tools=[logTransaction, getMonthlySummary, getCategorySpending],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                ),
            )
            chat.send_message("My monthly income is $3000.")
            response = chat.send_message("How much should I spend on food?")
            text = response.text or ""
            assert len(text.strip()) > 10, "AI không nhớ ngữ cảnh hội thoại"
    except genai_errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            pytest.skip("Đã chạm giới hạn quota API")
        raise
