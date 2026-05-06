# app/services/finance_service.py
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any, Optional

class FinanceService:

    #Quản lý ngân sách
    @staticmethod
    def set_category_budget(db, category: str, amount: float, month: Optional[str] = None) -> str:
        """Thiết lập ngân sách cho một category"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        query = """
            INSERT INTO budgets (category, amount, month)
            VALUES (:category, :amount, :month)
            ON CONFLICT(category) DO UPDATE 
            SET amount = excluded.amount, month = excluded.month
        """
        db.execute(text(query), {"category": category, "amount": amount, "month": month})
        db.commit()
        
        return f"✅ Đã đặt ngân sách **{amount:,.0f} VND** cho category **{category}** tháng {month}."

    #Thống kê chi tiêu
    @staticmethod
    def get_monthly_summary(db) -> Dict:
        """Tóm tắt chi tiêu tháng hiện tại"""
        month = datetime.now().strftime("%Y-%m")
        
        query = """
            SELECT 
                Category,
                SUM(Amount) as spent,
                COUNT(*) as count
            FROM transactions 
            WHERE "Transaction Type" = 'debit' 
              AND Month = :month
            GROUP BY Category
        """
        result = db.execute(text(query), {"month": month}).fetchall()
        
        total_spent = sum(float(r.spent) for r in result)
        
        return {
            "month": month,
            "total_spent": round(total_spent, 2),
            "by_category": {r.Category: round(float(r.spent), 2) for r in result},
            "transaction_count": sum(int(r.count) for r in result)
        }

    @staticmethod
    def get_category_spending(db, category: str) -> Dict:
        """Chi tiêu theo category cụ thể"""
        month = datetime.now().strftime("%Y-%m")
        
        query = """
            SELECT COALESCE(SUM(Amount), 0) as spent, COUNT(*) as count
            FROM transactions 
            WHERE "Transaction Type" = 'debit' 
              AND Month = :month 
              AND Category = :category
        """
        result = db.execute(text(query), {"month": month, "category": category}).fetchone()
        
        return {
            "category": category,
            "spent": round(float(result.spent), 2),
            "count": int(result.count)
        }

    @staticmethod
    def get_category_income(db, category: str) -> Dict:
        """Thu nhập theo category cụ thể"""
        # Sử dụng tháng hiện tại làm mặc định
        month = datetime.now().strftime("%Y-%m")
        
        # Truy vấn SQL: Tính tổng số tiền (earned) và số lượng giao dịch (count) cho thu nhập (credit)
        query = """
            SELECT COALESCE(SUM(Amount), 0) as earned, COUNT(*) as count
            FROM transactions 
            WHERE "Transaction Type" = 'credit' 
              AND Month = :month 
              AND Category = :category
        """
        # Thực thi truy vấn và lấy dòng dữ liệu kết quả đầu tiên
        result = db.execute(text(query), {"month": month, "category": category}).fetchone()
        
        # Đóng gói kết quả trả về dạng Dictionary
        return {
            "category": category,
            "earned": round(float(result.earned), 2),
            "count": int(result.count)
        }

    @staticmethod
    def list_categories_by_type(db, month: Optional[str] = None) -> Dict:
        """Danh sách category phân loại theo income (thu) và outcome (chi)"""
        # Nếu không chỉ định tháng, sẽ lấy tháng hiện tại
        if month is None:
            month = datetime.now().strftime("%Y-%m")
            
        # Truy vấn SQL: Lấy danh sách danh mục (Category) và loại giao dịch của chúng trong tháng
        query = """
            SELECT Category, "Transaction Type" as type
            FROM transactions
            WHERE Month = :month
            GROUP BY Category, "Transaction Type"
        """
        results = db.execute(text(query), {"month": month}).fetchall()
        
        # Tách danh sách thành 2 mảng: một cho thu nhập (credit) và một cho chi tiêu (debit)
        income_categories = [r.Category for r in results if r.type == 'credit']
        outcome_categories = [r.Category for r in results if r.type == 'debit']
        
        return {
            "month": month,
            "income_categories": income_categories,
            "outcome_categories": outcome_categories
        }

    #Cảnh báo ngân sách
    @staticmethod
    def check_budget_warning(db) -> Dict[str, Any]:
        """Kiểm tra cảnh báo khi vượt 80% ngân sách"""
        month = datetime.now().strftime("%Y-%m")
        
        # Lấy ngân sách
        budgets = db.execute(text("SELECT category, amount FROM budgets WHERE month = :month"), 
                           {"month": month}).fetchall()
        
        # Lấy chi tiêu thực tế
        spending = db.execute(text("""
            SELECT Category, SUM(Amount) as spent 
            FROM transactions 
            WHERE "Transaction Type" = 'debit' AND Month = :month 
            GROUP BY Category
        """), {"month": month}).fetchall()
        
        spending_dict = {r.Category: float(r.spent) for r in spending}
        warnings = []
        total_budget = 0
        total_spent = 0

        for b in budgets:
            cat = b.category
            budget = float(b.amount)
            spent = spending_dict.get(cat, 0)
            total_budget += budget
            total_spent += spent

            if budget > 0 and (spent / budget) >= 0.80:
                percent = (spent / budget) * 100
                warnings.append({
                    "category": cat,
                    "budget": budget,
                    "spent": spent,
                    "percent": round(percent, 1),
                    "message": f"⚠️ **{cat}**: Đã chi {percent:.1f}% ngân sách ({spent:,.0f}/{budget:,.0f} VND)"
                })

        return {
            "has_warning": len(warnings) > 0,
            "warnings": warnings,
            "total_budget": round(total_budget, 2),
            "total_spent": round(total_spent, 2),
            "overall_percent": round((total_spent / total_budget * 100) if total_budget > 0 else 0, 1)
        }