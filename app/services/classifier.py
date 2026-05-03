# classifier.py
# Module phan loai text chi tieu vao category
# Tuan 2 - Mini Project 

import re
import sys
import io
from typing import Optional

# Fix Windows console encoding for Vietnamese
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ===== KEYWORD MAPPING =====
# Map keywords -> category
CATEGORY_KEYWORDS = {
    'Food': [
        'ăn', 'eat', 'food', 'lunch', 'dinner', 'breakfast', 'snack',
        'cơm', 'phở', 'bún', 'mì', 'cafe', 'coffee', 'trà', 'tea',
        'bánh', 'pizza', 'burger', 'chicken', 'rice', 'noodle',
        'restaurant', 'nhà hàng', 'quán', 'canteen', 'bữa',
        'uống', 'drink', 'nước', 'juice', 'milk', 'sữa',
        'grab food', 'shopee food', 'now', 'gofood', 'baemin',
    ],
    'Transport': [
        'grab', 'taxi', 'xe', 'bus', 'xăng', 'fuel', 'gas', 'petrol',
        'parking', 'đỗ xe', 'gửi xe', 'toll', 'vé', 'ticket',
        'uber', 'gojek', 'be', 'transport', 'di chuyển', 'commute',
        'train', 'tàu', 'metro', 'flight', 'bay', 'máy bay',
    ],
    'Entertainment': [
        'movie', 'phim', 'cinema', 'game', 'netflix', 'spotify',
        'giải trí', 'entertainment', 'karaoke', 'bar', 'pub', 'club',
        'concert', 'show', 'du lịch', 'travel', 'tour', 'resort',
        'gym', 'sport', 'thể thao', 'swimming', 'bơi',
    ],
    'Shopping': [
        'mua', 'buy', 'shop', 'shopping', 'quần áo', 'clothes',
        'shoes', 'giày', 'bag', 'túi', 'accessories', 'phụ kiện',
        'lazada', 'shopee', 'tiki', 'amazon', 'online',
        'thời trang', 'fashion', 'đồ', 'item',
    ],
    'Bills': [
        'điện', 'electric', 'nước', 'water', 'internet', 'wifi',
        'phone', 'điện thoại', 'bill', 'hóa đơn', 'rent', 'thuê',
        'nhà', 'house', 'apartment', 'insurance', 'bảo hiểm',
        'subscription', 'đăng ký', 'trả góp', 'installment',
    ],
    'Healthcare': [
        'doctor', 'bác sĩ', 'hospital', 'bệnh viện', 'thuốc',
        'medicine', 'pharmacy', 'khám', 'health', 'sức khỏe',
        'dental', 'nha khoa', 'eye', 'mắt', 'clinic', 'phòng khám',
    ],
    'Education': [
        'học', 'study', 'school', 'trường', 'course', 'khóa học',
        'book', 'sách', 'tuition', 'học phí', 'class', 'lớp',
        'udemy', 'coursera', 'tutorial', 'training',
    ],
    'Grocery': [
        'grocery', 'siêu thị', 'supermarket', 'chợ', 'market',
        'thực phẩm', 'rau', 'vegetable', 'fruit', 'trái cây',
        'meat', 'thịt', 'fish', 'cá', 'egg', 'trứng',
        'winmart', 'coopmart', 'bach hoa xanh', 'bách hóa',
    ],
    'Income': [
        'salary', 'lương', 'income', 'thu nhập', 'bonus', 'thưởng',
        'refund', 'hoàn tiền', 'transfer in', 'nhận', 'receive',
        'dividend', 'cổ tức', 'interest', 'lãi',
    ],
}


def classify_transaction(description: str, amount: Optional[float] = None) -> str:
    """
    Phan loai text mo ta chi tieu vao category phu hop.
    Su dung keyword matching.
    
    Args:
        description: Mo ta giao dich (VD: "An trua voi ban")
        amount: So tien (positive = income, negative = expense)
    
    Returns:
        Category name (str)
    """
    if not description:
        return 'Other'
    
    text = description.lower().strip()
    
    # Neu amount > 0, co the la income
    if amount is not None and amount > 0:
        for keyword in CATEGORY_KEYWORDS['Income']:
            if keyword in text:
                return 'Income'
        # Default positive amounts to Income if no other match
        return 'Income'
    
    # Tim category co nhieu keyword match nhat
    best_category = 'Other'
    best_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == 'Income':
            continue  # Da xu ly o tren
        
        score = 0
        for keyword in keywords:
            if keyword in text:
                # Keyword dai hon duoc uu tien hon
                score += len(keyword)
        
        if score > best_score:
            best_score = score
            best_category = category
    
    return best_category


def classify_batch(descriptions: list, amounts: Optional[list] = None) -> list:
    """
    Phan loai nhieu giao dich cung luc.
    
    Args:
        descriptions: List cac mo ta giao dich
        amounts: List so tien tuong ung (optional)
    
    Returns:
        List category tuong ung
    """
    results = []
    for i, desc in enumerate(descriptions):
        amt = amounts[i] if amounts and i < len(amounts) else None
        results.append(classify_transaction(desc, amt))
    return results


def get_all_categories() -> list:
    """Tra ve danh sach tat ca categories."""
    return list(CATEGORY_KEYWORDS.keys()) + ['Other']


def add_custom_keywords(category: str, keywords: list):
    """Them keywords tu dinh nghia cho mot category."""
    if category not in CATEGORY_KEYWORDS:
        CATEGORY_KEYWORDS[category] = []
    CATEGORY_KEYWORDS[category].extend(keywords)


# ===== TEST =====
if __name__ == '__main__':
    test_cases = [
        ("Ăn trưa với bạn", -50000),
        ("Grab taxi đi làm", -30000),
        ("Lương tháng 1", 10000000),
        ("Mua quần áo Shopee", -350000),
        ("Tiền điện tháng 1", -500000),
        ("Khám bệnh viện", -200000),
        ("Xem phim CGV", -100000),
        ("Mua rau siêu thị", -80000),
        ("Học phí khóa Python", -2000000),
        ("Coffee Highlands", -45000),
        ("Netflix subscription", -200000),
        ("Đổ xăng xe máy", -100000),
        ("Thưởng Tết", 5000000),
        ("Random transaction", -50000),
    ]
    
    print("=" * 65)
    print("  TEXT CLASSIFICATION TEST")
    print("=" * 65)
    print(f"{'Description':<30} {'Amount':>12} {'Category':<15}")
    print("-" * 65)
    
    for desc, amount in test_cases:
        category = classify_transaction(desc, amount)
        print(f"{desc:<30} {amount:>12,.0f} {category:<15}")
    
    print(f"\n{'=' * 65}")
    print(f"Available categories: {get_all_categories()}")
