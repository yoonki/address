import streamlit as st
import re

# 정규표현식 패턴들을 미리 컴파일 (성능 최적화)
PATTERNS = {
    'product': re.compile(r'상품명(.*?)상품주문상태', re.DOTALL),
    'option': re.compile(r'옵션(.*?)주문수량', re.DOTALL),
    'order_quantity': re.compile(r'주문수량\s*([0-9,]+)', re.DOTALL),
    'recipient': re.compile(r'수취인명(.*?)연락처1(.*?)연락처2', re.DOTALL),
    'delivery': re.compile(r'배송지([가-힣\s\d\-\(\),\.]+)\s*배송메모', re.DOTALL),
    'phone': re.compile(r'^\d{3}-\d{4}-\d{4}$'),
    'cleanup_whitespace': re.compile(r'\s+'),
    'cleanup_newlines': re.compile(r'\n\s*\n')
}

# 시스템 키워드들 (성능을 위해 set 사용)
SYSTEM_KEYWORDS = {
    '정보', '배송지 정보', '수취인명', '연락처1', '연락처2', '배송지'
}

def clean_text_format(text):
    """텍스트 서식을 정리하는 통합 함수"""
    if not text:
        return text
    
    # 특수 문자들을 한 번에 처리
    replacements = {
        '\u00a0': ' ',    # Non-breaking space
        '\u2009': ' ',    # Thin space
        '\u200b': '',     # Zero-width space
        '\u200c': '',     # Zero-width non-joiner
        '\u200d': '',     # Zero-width joiner
        '\ufeff': '',     # Byte order mark
        '\\\\n': '\n',    # Double escaped newlines
        '\\n': '\n',      # Escaped newlines
        '\t': ' '         # Tabs to spaces
    }
    
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # 정규표현식으로 마지막 정리
    cleaned = PATTERNS['cleanup_newlines'].sub('\n', cleaned)
    cleaned = PATTERNS['cleanup_whitespace'].sub(' ', cleaned)
    
    return cleaned.strip()

def extract_between_patterns(text, pattern_key, error_msg="정보를 찾을 수 없습니다"):
    """공통 패턴 추출 함수"""
    try:
        match = PATTERNS[pattern_key].search(text)
        return match.group(1).strip() if match else error_msg
    except Exception as e:
        st.error(f"추출 중 오류 발생 ({pattern_key}): {str(e)}")
        return error_msg

def extract_product_info(text):
    """상품 정보 추출"""
    return extract_between_patterns(text, 'product', "상품명을 찾을 수 없습니다")

def extract_option_order_quantity(text):
    """옵션 정보 추출"""
    try:
        matches = PATTERNS['option'].findall(text)
        return matches if matches else ["옵션 정보를 찾을 수 없습니다"]
    except Exception as e:
        st.error(f"옵션 추출 중 오류: {str(e)}")
        return ["옵션 정보를 찾을 수 없습니다"]

def extract_order_quantity_amount(text):
    """주문수량 추출"""
    try:
        match = PATTERNS['order_quantity'].search(text)
        if match:
            return f"주문수량 : {match.group(1).replace(',', '')}"
        return "주문수량을 찾을 수 없습니다"
    except Exception as e:
        st.error(f"주문수량 추출 중 오류: {str(e)}")
        return "주문수량을 찾을 수 없습니다"

def extract_recipient_info(text):
    """수취인 정보 추출"""
    try:
        match = PATTERNS['recipient'].search(text)
        if match:
            recipient_name = match.group(1).strip()
            contact1 = match.group(2).strip()
            
            # 전화번호 유효성 검사
            if not PATTERNS['phone'].match(contact1):
                st.warning("전화번호 형식이 올바르지 않을 수 있습니다")
            
            return recipient_name, contact1
        return "수취인 정보를 찾을 수 없습니다", ""
    except Exception as e:
        st.error(f"수취인 정보 추출 중 오류: {str(e)}")
        return "수취인 정보 추출 오류", ""

def clean_address_text(address, recipient_name, contact1):
    """주소 텍스트 정리 (최적화된 버전)"""
    # 수취인 정보 제거
    if recipient_name and "찾을 수 없습니다" not in recipient_name:
        address = address.replace(recipient_name, '')
    if contact1:
        address = address.replace(contact1, '')
    
    # 시스템 키워드들을 한 번에 제거 (set을 사용한 효율적인 검색)
    for keyword in SYSTEM_KEYWORDS:
        address = address.replace(keyword, ' ')
    
    # 최종 정리
    return PATTERNS['cleanup_whitespace'].sub(' ', address).strip()

def extract_delivery_info(text, recipient_name, contact1):
    """배송지 정보 추출 (최적화된 버전)"""
    try:
        match = PATTERNS['delivery'].search(text)
        if not match:
            return "배송지를 찾을 수 없습니다"
        
        address = match.group(1).strip()
        cleaned_address = clean_address_text(address, recipient_name, contact1)
        
        return cleaned_address if cleaned_address else "배송지를 찾을 수 없습니다"
    except Exception as e:
        st.error(f"배송지 추출 중 오류: {str(e)}")
        return "배송지 추출 오류"

def validate_extraction_results(results):
    """추출 결과 검증"""
    warnings = []
    
    if "찾을 수 없습니다" in results.get('product', ''):
        warnings.append("상품명을 찾지 못했습니다")
    
    if not results.get('recipient_name') or "찾을 수 없습니다" in results['recipient_name']:
        warnings.append("수취인명을 찾지 못했습니다")
    
    if not results.get('contact1') or not PATTERNS['phone'].match(results['contact1']):
        warnings.append("올바르지 않은 전화번호입니다")
    
    if "찾을 수 없습니다" in results.get('delivery', ''):
        warnings.append("배송지를 찾지 못했습니다")
    
    return warnings

def process_text_extraction(text, remove_formatting=True):
    """텍스트 추출 처리 통합 함수"""
    # 서식 제거
    processed_text = clean_text_format(text) if remove_formatting else text
    
    # 정보 추출
    results = {
        'product': extract_product_info(processed_text),
        'options': extract_option_order_quantity(processed_text),
        'order_quantity': extract_order_quantity_amount(processed_text),
        'recipient_name': None,
        'contact1': None,
        'delivery': None
    }
    
    # 수취인 정보 추출
    results['recipient_name'], results['contact1'] = extract_recipient_info(processed_text)
    
    # 배송지 정보 추출
    results['delivery'] = extract_delivery_info(processed_text, results['recipient_name'], results['contact1'])
    
    # 서식 제거 적용 (결과에도)
    if remove_formatting:
        results['product'] = clean_text_format(results['product'])
        results['options'] = [clean_text_format(opt) for opt in results['options']]
        results['order_quantity'] = clean_text_format(results['order_quantity'])
        results['recipient_name'] = clean_text_format(results['recipient_name'])
        results['contact1'] = clean_text_format(results['contact1'])
        results['delivery'] = clean_text_format(results['delivery'])
    
    return results

def create_copy_text_areas(results):
    """복사용 텍스트 영역 생성"""
    # 전체 결과 텍스트 생성
    all_results = [
        results['product'],
        *results['options'],
        results['order_quantity'],
        results['recipient_name'],
        results['contact1'],
        results['delivery']
    ]
    
    # 유효한 결과만 필터링
    filtered_results = [
        result for result in all_results 
        if result and not any(error in result for error in ["찾을 수 없습니다", "오류"])
    ]
    
    final_text = '\n'.join(filtered_results)
    
    # 메인 복사 영역
    st.text_area(
        "📋 추출된 정보 (Ctrl+A → Ctrl+C로 복사):",
        value=final_text,
        height=200,
        key="main_copy_text",
        help="텍스트 영역 클릭 → Ctrl+A (전체 선택) → Ctrl+C (복사)"
    )

def main():
    st.title("🏪 스마트스토어 주문 정보 추출기")
    st.markdown("---")
    
    # 옵션 설정
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📝 주문 정보 입력")
    with col2:
        remove_formatting = st.checkbox("서식 자동 제거", value=True, 
                                      help="애플 메일 등에서 복사한 텍스트의 서식을 자동으로 제거합니다")
    
    # 텍스트 입력
    text = st.text_area("주문 정보를 붙여넣으세요:", height=300, 
                       placeholder="스마트스토어에서 복사한 주문 정보를 여기에 붙여넣으세요...")
    
    # 처리 버튼
    if st.button("🔍 정보 추출하기", type="primary", use_container_width=True):
        if not text.strip():
            st.error("텍스트를 입력해주세요!")
            return
        
        with st.spinner("정보를 추출하는 중..."):
            # 정보 추출
            results = process_text_extraction(text, remove_formatting)
            
            # 결과 검증 및 경고 표시
            warnings = validate_extraction_results(results)
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
            
            # 추출된 정보 표시
            st.markdown("---")
            st.subheader("✅ 추출된 정보:")
            
            # 개별 결과 표시
            for result in [results['product']] + results['options'] + [results['order_quantity'], 
                          results['recipient_name'], results['contact1'], results['delivery']]:
                if result and not any(error in result for error in ["찾을 수 없습니다", "오류"]):
                    st.text(result)
            
            st.markdown("---")
            
            # 복사용 텍스트 영역들
            create_copy_text_areas(results)
            
            # 사용법 안내
            st.info("💡 **복사 방법**: 텍스트 영역 클릭 → **Ctrl+A** (전체 선택) → **Ctrl+C** (복사)")

if __name__ == "__main__":
    st.set_page_config(
        page_title="스마트스토어 주문 정보 추출기",
        page_icon="🏪",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    main()
