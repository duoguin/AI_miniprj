# statistics.py
# Module thong ke chi tieu ca nhan
# Tuan 2 - Mini Project 

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def load_transactions(csv_path: str) -> pd.DataFrame:
    """
    Load transaction data from CSV file.
    Expected columns: date, description, amount, category (optional)
    """
    df = pd.read_csv(csv_path)
    # Normalize column names to lowercase
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Parse date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], dayfirst=False, errors='coerce')
    
    # Ensure amount is numeric
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    return df


def total_spending(df: pd.DataFrame, category: Optional[str] = None) -> float:
    """Tinh tong chi tieu, co the loc theo category."""
    filtered = df.copy()
    if category and 'category' in filtered.columns:
        filtered = filtered[filtered['category'].str.lower() == category.lower()]
    
    # Chi tieu la so am (outflow) hoac tat ca
    if 'amount' in filtered.columns:
        spending = filtered[filtered['amount'] < 0]['amount'].sum()
        if spending == 0:
            spending = filtered['amount'].sum()
        return abs(spending)
    return 0.0


def spending_by_period(df: pd.DataFrame, period: str = 'month') -> pd.DataFrame:
    """
    Thong ke chi tieu theo ngay/tuan/thang.
    period: 'day', 'week', 'month'
    """
    if 'date' not in df.columns or 'amount' not in df.columns:
        return pd.DataFrame()
    
    filtered = df.copy()
    filtered = filtered.dropna(subset=['date', 'amount'])
    
    if period == 'day':
        filtered['period'] = filtered['date'].dt.date
    elif period == 'week':
        filtered['period'] = filtered['date'].dt.isocalendar().week
        filtered['year'] = filtered['date'].dt.year
        result = filtered.groupby(['year', 'period'])['amount'].agg(['sum', 'count', 'mean']).reset_index()
        result.columns = ['year', 'week', 'total', 'count', 'average']
        return result
    elif period == 'month':
        filtered['period'] = filtered['date'].dt.to_period('M')
    else:
        raise ValueError(f"Invalid period: {period}. Use 'day', 'week', or 'month'.")
    
    result = filtered.groupby('period')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    result.columns = ['period', 'total', 'count', 'average']
    return result


def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Thong ke chi tieu theo tung category."""
    if 'category' not in df.columns or 'amount' not in df.columns:
        return pd.DataFrame()
    
    result = df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    result.columns = ['category', 'total', 'count', 'average']
    result = result.sort_values('total', ascending=True)  # Most spending first (negative)
    return result


def spending_summary(df: pd.DataFrame) -> dict:
    """Tong hop thong ke chi tieu."""
    summary = {
        'total_transactions': len(df),
        'total_spending': total_spending(df),
        'average_per_transaction': df['amount'].mean() if 'amount' in df.columns else 0,
        'max_transaction': df['amount'].min() if 'amount' in df.columns else 0,  # Most negative = biggest spend
        'min_transaction': df['amount'].max() if 'amount' in df.columns else 0,
    }
    
    if 'category' in df.columns:
        summary['num_categories'] = df['category'].nunique()
        top_cat = spending_by_category(df)
        if not top_cat.empty:
            summary['top_category'] = top_cat.iloc[0]['category']
            summary['top_category_total'] = abs(top_cat.iloc[0]['total'])
    
    if 'date' in df.columns:
        summary['date_range'] = {
            'from': str(df['date'].min()),
            'to': str(df['date'].max()),
        }
    
    return summary


def check_budget(df: pd.DataFrame, budget: float, period: str = 'month') -> list:
    """
    Kiem tra chi tieu co vuot qua ngan sach khong.
    Tra ve danh sach cac period vuot budget.
    """
    period_spending = spending_by_period(df, period)
    if period_spending.empty:
        return []
    
    warnings = []
    for _, row in period_spending.iterrows():
        spent = abs(row['total'])
        if spent > budget:
            warnings.append({
                'period': str(row.get('period', row.get('week', ''))),
                'spent': spent,
                'budget': budget,
                'over_by': spent - budget,
                'percentage': (spent / budget) * 100
            })
        elif spent > budget * 0.8:  # Canh bao khi dat 80%
            warnings.append({
                'period': str(row.get('period', row.get('week', ''))),
                'spent': spent,
                'budget': budget,
                'remaining': budget - spent,
                'percentage': (spent / budget) * 100,
                'warning': 'APPROACHING_LIMIT'
            })
    
    return warnings


def get_balance(df: pd.DataFrame) -> float:
    """Tinh so du hien tai (tong income - tong spending)."""
    if 'amount' not in df.columns:
        return 0.0
    return df['amount'].sum()


# ===== TEST =====
if __name__ == '__main__':
    # Tao sample data de test
    sample_data = {
        'date': ['2024-01-05', '2024-01-10', '2024-01-15', '2024-01-20',
                 '2024-02-01', '2024-02-10', '2024-02-15', '2024-02-20'],
        'description': ['Lunch', 'Salary', 'Grab taxi', 'Coffee shop',
                        'Grocery', 'Salary', 'Electric bill', 'Movie'],
        'amount': [-50000, 10000000, -30000, -25000,
                   -200000, 10000000, -500000, -100000],
        'category': ['Food', 'Income', 'Transport', 'Food',
                     'Grocery', 'Income', 'Bills', 'Entertainment']
    }
    
    df = pd.DataFrame(sample_data)
    df['date'] = pd.to_datetime(df['date'])
    
    print("=== SPENDING SUMMARY ===")
    summary = spending_summary(df)
    for k, v in summary.items():
        print(f"  {k}: {v}")
    
    print("\n=== SPENDING BY CATEGORY ===")
    print(spending_by_category(df).to_string(index=False))
    
    print("\n=== SPENDING BY MONTH ===")
    print(spending_by_period(df, 'month').to_string(index=False))
    
    print("\n=== BUDGET CHECK (500,000/month) ===")
    warnings = check_budget(df, 500000, 'month')
    for w in warnings:
        print(f"  {w}")
    
    print(f"\n=== BALANCE: {get_balance(df):,.0f} ===")
