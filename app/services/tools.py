import csv
from config import DATA_FILE
from utils.time_utils import getCurrentDate, getCurrentMonth, normalizeDate, extractMonthFromDate

def logTransaction(
    date: str,
    description: str,
    amount: float,
    transactionType: str,
    category: str,
    accountName: str
) -> str:
    """
    REQUIRED: Call this tool when the user wants to log, save, or record a new expense or income.

    STRICT RULES:
    - amount MUST be positive
    - transactionType MUST be 'debit' or 'credit'
    - date MUST be YYYY-MM-DD

    Args:
        date: Transaction date
        description: Description
        amount: Positive number
        transactionType: debit | credit
        category: Category name
        accountName: Payment method
    """

    if transactionType not in ["debit", "credit"]:
        return "ERROR: transactionType must be 'debit' or 'credit'."

    if amount <= 0:
        return "ERROR: amount must be positive."

    if not accountName:
        accountName = "null"

    date = normalizeDate(date)

    if len(date) != 10:
        return "ERROR: Invalid date format. Must be YYYY-MM-DD."

    month = extractMonthFromDate(date)

    try:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow([
                    "Date",
                    "Description",
                    "Amount",
                    "Transaction Type",
                    "Category",
                    "Account Name",
                    "Month"
                ])

            writer.writerow([
                date,
                description,
                amount,
                transactionType,
                category,
                accountName,
                month
            ])

        return f"SUCCESS: Recorded {amount} for {description} ({category}) via {accountName} on {date}."

    except Exception as e:
        return f"ERROR: Could not save transaction. {e}"


def getMonthlySummary(month: str) -> str:
    """
    REQUIRED: Call this tool when user asks for total income, expense, or balance.

    Args:
        month: YYYY-MM
    """

    if not month:
        month = getCurrentMonth()

    totalExpense = 0.0
    totalIncome = 0.0

    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row['Month'] == month:
                    amount = float(row['Amount'])

                    if row['Transaction Type'] == 'debit':
                        totalExpense += amount
                    elif row['Transaction Type'] == 'credit':
                        totalIncome += amount

        balance = totalIncome - totalExpense

        return (
            f"REPORT {month}: "
            f"Income={totalIncome}, "
            f"Expense={totalExpense}, "
            f"Balance={balance}"
        )

    except FileNotFoundError:
        return "WARNING: No data found."


def getCategorySpending(month: str, category: str) -> str:
    """
    REQUIRED: Call when user asks spending for a category.

    Args:
        month: YYYY-MM
        category: category name
    """

    if not month:
        month = getCurrentMonth()

    total = 0.0
    details = []

    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if (
                    row['Month'] == month and
                    row['Category'].lower() == category.lower() and
                    row['Transaction Type'] == 'debit'
                ):
                    amount = float(row['Amount'])
                    total += amount
                    details.append(f"{row['Description']} ({amount})")

        return (
            f"CATEGORY REPORT {month} - {category}: "
            f"Total={total}, Details={', '.join(details) if details else 'None'}"
        )

    except FileNotFoundError:
        return "WARNING: No data found."


def getCategoryIncome(month: str, category: str) -> str:
    """
    BẮT BUỘC: Gọi tool này khi người dùng muốn biết tổng thu nhập (income) cho một danh mục (category) cụ thể.

    Args:
        month: Tháng cần xem (YYYY-MM)
        category: Tên danh mục (category)
    """

    # Nếu không truyền tháng, mặc định lấy tháng hiện tại
    if not month:
        month = getCurrentMonth()

    total = 0.0
    details = []

    try:
        # Mở file CSV để đọc dữ liệu
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Lặp qua từng dòng dữ liệu trong CSV
            for row in reader:
                # Kiểm tra đúng tháng, đúng category và loại giao dịch phải là 'credit' (thu nhập)
                if (
                    row['Month'] == month and
                    row['Category'].lower() == category.lower() and
                    row['Transaction Type'] == 'credit'
                ):
                    amount = float(row['Amount'])
                    total += amount
                    # Lưu lại chi tiết từng khoản thu nhập
                    details.append(f"{row['Description']} ({amount})")

        # Trả về kết quả báo cáo dưới dạng chuỗi
        return (
            f"BÁO CÁO THU NHẬP {month} - {category}: "
            f"Tổng cộng={total}, Chi tiết={', '.join(details) if details else 'Không có'}"
        )

    except FileNotFoundError:
        return "CẢNH BÁO: Không tìm thấy dữ liệu."


def listCategoriesByType(month: str) -> str:
    """
    BẮT BUỘC: Gọi tool này khi người dùng muốn xem danh sách các danh mục (category) đã được sử dụng, phân loại theo thu nhập (income) và chi tiêu (expense).
    
    Args:
        month: Tháng cần xem (YYYY-MM)
    """
    # Nếu không truyền tháng, mặc định lấy tháng hiện tại
    if not month:
        month = getCurrentMonth()

    # Khởi tạo tập hợp (set) để lưu danh mục nhằm tránh trùng lặp
    income_categories = set()
    expense_categories = set()

    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Chỉ lấy các giao dịch trong tháng được yêu cầu
                if row['Month'] == month:
                    if row['Transaction Type'] == 'credit':
                        income_categories.add(row['Category'])
                    elif row['Transaction Type'] == 'debit':
                        expense_categories.add(row['Category'])

        # Trả về chuỗi kết quả gồm 2 danh sách
        return (
            f"DANH MỤC TRONG THÁNG {month}:\n"
            f"Thu nhập (Income): {', '.join(income_categories) if income_categories else 'Không có'}\n"
            f"Chi tiêu (Expense): {', '.join(expense_categories) if expense_categories else 'Không có'}"
        )

    except FileNotFoundError:
        return "CẢNH BÁO: Không tìm thấy dữ liệu."


def setCategoryBudget(category: str, amount: float, month: str) -> str:
    """
    REQUIRED: Call when user sets budget for a category.

    Args:
        category: category name
        amount: budget
        month: YYYY-MM
    """

    if not month:
        month = getCurrentMonth()

    try:
        with open("budgets.csv", mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(["Category", "Amount", "Month"])

            writer.writerow([category, amount, month])

        return f"SUCCESS: Budget set {amount} for {category} in {month}"

    except Exception as e:
        return f"ERROR: {e}"


def getCurrentTime() -> str:
    """
    REQUIRED: Call this tool when current datetime is needed.

    Returns:
        ISO datetime string
    """
    from time_utils import getCurrentDateTime
    return getCurrentDateTime()

