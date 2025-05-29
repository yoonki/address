import streamlit as st
import re

# 정규표현식 패턴들을 미리 컴파일 (성능 최적화)
PATTERNS = {
    'product': re.compile(r'상품명(.*?)상품주문상태', re.DOTALL),
    'option': re.compile(r'옵션(.*?)주문수량', re.DOTALL),
    'order_quantity': re.compile(r'주문수량\s*([0-9,]+)', re.DOTALL),
    'recipient': re.compile(r'수취인명(.*?)연락처1(.*?)연락처2', re.DOTALL),
    'delivery': re.compile(r'배송지(.*?)배송메모', re.DOTALL),
    'phone': re.compile(r'^\d{3}-\d{4}-\d{4}$'),
    'cleanup_whitespace': re.compile(r'\s+'),
    'cleanup_newlines': re.compile(r'\n\s*\n')
}

# 시스템 키워드들 (성능을 위해 set 사용)
SYSTEM_KEYWORDS = {
    '정보', '배송지 정보', '수취인명', '연락처1', '연락처2', '배송지'
}

def apply_responsive_css():
    """반응형 CSS 스타일 적용"""
    st.markdown("""
    <style>
        /* 전체 컨테이너 스타일 개선 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* 모바일 대응 (768px 이하) */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem 0.5rem !important;
                max-width: 100% !important;
            }
            
            /* 텍스트 영역 최적화 */
            .stTextArea textarea {
                font-size: 16px !important;
                line-height: 1.4 !important;
                padding: 12px !important;
            }
            
            /* 버튼 최적화 */
            .stButton button {
                width: 100% !important;
                height: 3rem !important;
                font-size: 18px !important;
                font-weight: bold !important;
                margin: 0.5rem 0 !important;
                border-radius: 25px !important;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
            }
            
            .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
            }
            
            /* 체크박스 영역 최적화 */
            .stCheckbox {
                font-size: 16px !important;
                margin: 1rem 0 !important;
            }
            
            /* 제목 크기 조정 */
            h1 {
                font-size: 24px !important;
                text-align: center !important;
            }
            
            h2, h3 {
                font-size: 18px !important;
            }
            
            /* 코드 블록 최적화 */
            .stCode {
                font-size: 14px !important;
            }
            
            /* 정보 박스 최적화 */
            .stAlert {
                font-size: 14px !important;
                padding: 12px !important;
                margin: 0.5rem 0 !important;
            }
        }
        
        /* 태블릿 대응 (769px ~ 1024px) */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                padding: 1.5rem 1rem !important;
                max-width: 95% !important;
            }
            
            .stTextArea textarea {
                font-size: 15px !important;
            }
            
            .stButton button {
                width: 100% !important;
                height: 2.5rem !important;
                font-size: 16px !important;
                border-radius: 20px !important;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
                border: none !important;
                color: white !important;
            }
        }
        
        /* 데스크톱 대응 (1025px 이상) */
        @media (min-width: 1025px) {
            .stButton button {
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
                border: none !important;
                border-radius: 25px !important;
                color: white !important;
                font-weight: bold !important;
                padding: 0.5rem 2rem !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
            }
        }
        
        /* 공통 스타일 개선 */
        .stTextArea textarea {
            border-radius: 10px !important;
            border: 2px solid #e0e0e0 !important;
            transition: border-color 0.3s ease !important;
        }
        
        .stTextArea textarea:focus {
            border-color: #4ECDC4 !important;
            box-shadow: 0 0 10px rgba(78, 205, 196, 0.3) !important;
        }
        
        /* 코드 블록 스타일 개선 */
        .stCode {
            border-radius: 10px !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        /* 체크박스 스타일 개선 */
        .stCheckbox > label {
            font-weight: 500 !important;
            color: #333 !important;
        }
        
        /* 성공/경고 메시지 스타일 */
        .stSuccess {
            border-radius: 10px !important;
            border-left: 5px solid #4CAF50 !important;
        }
        
        .stWarning {
            border-radius: 10px !important;
            border-left: 5px solid #FF9800 !important;
        }
        
        .stError {
            border-radius: 10px !important;
            border-left: 5px solid #F44336 !important;
        }
        
        .stInfo {
            border-radius: 10px !important;
            border-left: 5px solid #2196F3 !important;
        }
    </style>
    """, unsafe_allow_html=True)

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
    """배송지 정보 추출 (단순화된 버전)"""
    try:
        match = PATTERNS['delivery'].search(text)
        
        if match:
            raw_delivery_text = match.group(1).strip()
            cleaned_address = clean_address_text(raw_delivery_text, recipient_name, contact1)
            
            if len(cleaned_address) > 5:
                return cleaned_address
            else:
                return "배송지 정보가 부족합니다"
        
        return "배송지를 찾을 수 없습니다"
        
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
    
    # st.code를 사용하여 복사 기능 제공
    st.subheader("📋 추출된 정보")
    st.info("💡 **복사 방법**: 아래 박스 우상단의 복사 버튼을 클릭하거나 텍스트를 선택해서 복사하세요!")
    st.code(final_text, language=None)

def main():
    # 반응형 CSS 적용
    apply_responsive_css()
    
    st.title("🏪 스마트스토어 주문 정보 추출기")
    st.markdown("---")
    
    # 모바일에서는 단일 컬럼, 데스크톱에서는 2컬럼 레이아웃
    # 반응형을 위해 조건부 레이아웃 사용
    st.markdown("### 📝 주문 정보 입력")
    
    # 텍스트 입력
    text = st.text_area(
        "주문 정보를 붙여넣으세요:",
        height=300, 
        placeholder="스마트스토어에서 복사한 주문 정보를 여기에 붙여넣으세요...",
        help="복사한 텍스트를 그대로 붙여넣으면 됩니다"
    )
    
    # 옵션 설정 (모바일에서도 잘 보이도록)
    remove_formatting = st.checkbox(
        "서식 자동 제거", 
        value=True, 
        help="애플 메일 등에서 복사한 텍스트의 서식을 자동으로 제거합니다"
    )
    
    # 처리 버튼
    if st.button("🔍 정보 추출하기", type="primary", use_container_width=True):
        if not text.strip():
            st.error("📝 텍스트를 입력해주세요!")
            return
        
        with st.spinner("🔄 정보를 추출하는 중..."):
            # 정보 추출
            results = process_text_extraction(text, remove_formatting)
            
            # 결과 검증 및 경고 표시
            warnings = validate_extraction_results(results)
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
            
            st.markdown("---")
            
            # 복사용 텍스트 영역 (메인 결과)
            create_copy_text_areas(results)
            
            # 성공 메시지
            st.success("✅ 정보 추출 완료! 위의 복사 버튼을 이용해 정보를 복사하세요.")
    
    # 사용법 안내 (모바일에서도 잘 보이도록)
    with st.expander("ℹ️ 사용법 및 도움말"):
        st.markdown("""
        ### 📖 사용법
        1. **스마트스토어**에서 주문 정보를 복사
        2. 위 텍스트 박스에 **붙여넣기**
        3. **🔍 정보 추출하기** 버튼 클릭
        4. 추출된 정보를 **복사**해서 사용
        
        ### ✨ 자동으로 추출되는 정보
        - 📦 상품명
        - 🎯 옵션 정보  
        - 📊 주문수량
        - 👤 수취인명
        - 📞 연락처
        - 🏠 배송지 주소
        
        ### 💡 팁
        - 복사 버튼이 안 보이면 텍스트를 직접 선택해서 복사하세요
        - 서식이 이상하면 '서식 자동 제거' 옵션을 체크하세요
        - 정보가 제대로 추출되지 않으면 원본 텍스트를 다시 확인해보세요
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="🏪 스마트스토어 주문 정보 추출기",
        page_icon="🏪",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    main()
