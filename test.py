import streamlit as st
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from functools import lru_cache
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """추출 결과를 담는 데이터 클래스"""
    product: str
    options: List[str]
    order_quantity: str
    recipient_name: str
    contact1: str
    delivery: str
    warnings: List[str]
    is_valid: bool

class PatternManager:
    """정규표현식 패턴 관리 클래스"""
    
    def __init__(self):
        self._patterns = self._compile_patterns()
        self._system_keywords = frozenset([
            '정보', '배송지 정보', '수취인명', '연락처1', '연락처2', '배송지'
        ])
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """패턴들을 컴파일하여 반환"""
        patterns = {}
        
        # 각 패턴을 개별적으로 컴파일
        patterns['product'] = re.compile(r'상품명\s*(.*?)\s*상품주문상태', re.DOTALL)
        patterns['option'] = re.compile(r'옵션\s*(.*?)\s*주문수량', re.DOTALL)
        patterns['order_quantity'] = re.compile(r'주문수량\s*([0-9,]+)', re.DOTALL)
        patterns['recipient'] = re.compile(r'수취인명[\s\t]*(.*?)[\s\t]*연락처1[\s\t]*(.*?)[\s\t]*연락처2', re.DOTALL)
        patterns['delivery'] = re.compile(r'배송지[\s\t]+(.*?)[\s\t]*배송메모', re.DOTALL)
        patterns['delivery_alt'] = re.compile(r'배송지[\s\t]*([^\n\t]+(?:\n[^\t\n]+)*)', re.DOTALL)
        
        # 전화번호 패턴 (문법 오류 수정)
        phone_pattern = r'^\d{3}-\d{4}-\d{4}$'
        patterns['phone'] = re.compile(phone_pattern)
        
        # 정리용 패턴들
        patterns['cleanup_whitespace'] = re.compile(r'\s+')
        patterns['cleanup_newlines'] = re.compile(r'\n\s*\n')
        patterns['special_chars'] = re.compile(r'[\u00a0\u2009\u200b\u200c\u200d\ufeff]')
        patterns['cleanup_tabs'] = re.compile(r'\t+')
        
        return patterns
    
    @property
    def patterns(self) -> Dict[str, re.Pattern]:
        return self._patterns
    
    @property
    def system_keywords(self) -> frozenset:
        return self._system_keywords

class TextProcessor:
    """텍스트 처리 클래스"""
    
    def __init__(self, pattern_manager: PatternManager):
        self.pm = pattern_manager
        # 특수문자 변환 매핑
        self._char_replacements = (
            ('\u00a0', ' '),    # Non-breaking space
            ('\u2009', ' '),    # Thin space
            ('\u200b', ''),     # Zero-width space
            ('\u200c', ''),     # Zero-width non-joiner
            ('\u200d', ''),     # Zero-width joiner
            ('\ufeff', ''),     # Byte order mark
            ('\\\\n', '\n'),    # Double escaped newlines
            ('\\n', '\n'),      # Escaped newlines
            ('\t', ' ')         # Tabs to spaces
        )
    
    @lru_cache(maxsize=128)
    def clean_text_format(self, text: str) -> str:
        """텍스트 서식을 정리 (캐싱 적용)"""
        if not text:
            return text
        
        # 특수 문자 일괄 변환
        cleaned = text
        for old, new in self._char_replacements:
            cleaned = cleaned.replace(old, new)
        
        # 정규표현식으로 마지막 정리
        cleaned = self.pm.patterns['cleanup_newlines'].sub('\n', cleaned)
        cleaned = self.pm.patterns['cleanup_whitespace'].sub(' ', cleaned)
        cleaned = self.pm.patterns['cleanup_tabs'].sub(' ', cleaned)
        
        return cleaned.strip()
    
    def extract_by_pattern(self, text: str, pattern_key: str, 
                          error_msg: str = "정보를 찾을 수 없습니다") -> str:
        """패턴으로 텍스트 추출"""
        try:
            match = self.pm.patterns[pattern_key].search(text)
            return match.group(1).strip() if match else error_msg
        except Exception as e:
            logger.error(f"패턴 추출 오류 ({pattern_key}): {e}")
            return error_msg
    
    def clean_address_text(self, address: str, recipient_name: str, contact1: str) -> str:
        """주소 텍스트 정리"""
        # 탭 문자를 공백으로 변환
        address = address.replace('\t', ' ')
        
        # 수취인 정보 제거
        for info in [recipient_name, contact1]:
            if info and "찾을 수 없습니다" not in info:
                address = address.replace(info, '')
        
        # 시스템 키워드 제거
        for keyword in self.pm.system_keywords:
            address = address.replace(keyword, ' ')
        
        # 불필요한 공백 정리
        address = self.pm.patterns['cleanup_whitespace'].sub(' ', address)
        
        return address.strip()

class OrderExtractor:
    """주문 정보 추출 클래스"""
    
    def __init__(self):
        self.pm = PatternManager()
        self.tp = TextProcessor(self.pm)
    
    def extract_product_info(self, text: str) -> str:
        """상품 정보 추출"""
        return self.tp.extract_by_pattern(text, 'product', "상품명을 찾을 수 없습니다")
    
    def extract_options(self, text: str) -> List[str]:
        """옵션 정보 추출"""
        try:
            matches = self.pm.patterns['option'].findall(text)
            return [match.strip() for match in matches] if matches else ["옵션 정보를 찾을 수 없습니다"]
        except Exception as e:
            logger.error(f"옵션 추출 오류: {e}")
            return ["옵션 정보를 찾을 수 없습니다"]
    
    def extract_order_quantity(self, text: str) -> str:
        """주문수량 추출"""
        try:
            match = self.pm.patterns['order_quantity'].search(text)
            if match:
                return f"주문수량 : {match.group(1).replace(',', '')}"
            return "주문수량을 찾을 수 없습니다"
        except Exception as e:
            logger.error(f"주문수량 추출 오류: {e}")
            return "주문수량을 찾을 수 없습니다"
    
    def extract_recipient_info(self, text: str) -> Tuple[str, str]:
        """수취인 정보 추출"""
        try:
            match = self.pm.patterns['recipient'].search(text)
            if match:
                recipient_name = match.group(1).strip()
                contact1 = match.group(2).strip()
                return recipient_name, contact1
            return "수취인 정보를 찾을 수 없습니다", ""
        except Exception as e:
            logger.error(f"수취인 정보 추출 오류: {e}")
            return "수취인 정보 추출 오류", ""
    
    def extract_delivery_info(self, text: str, recipient_name: str, contact1: str) -> str:
        """배송지 정보 추출 (개선된 버전)"""
        try:
            # 첫 번째 패턴 시도 (배송메모까지)
            match = self.pm.patterns['delivery'].search(text)
            
            if match:
                raw_delivery_text = match.group(1).strip()
            else:
                # 두 번째 패턴 시도 (배송메모 없이)
                match = self.pm.patterns['delivery_alt'].search(text)
                if match:
                    raw_delivery_text = match.group(1).strip()
                else:
                    return "배송지를 찾을 수 없습니다"
            
            # 배송지 텍스트 정리
            cleaned_address = self.tp.clean_address_text(raw_delivery_text, recipient_name, contact1)
            
            # 빈 줄 제거 및 최종 정리
            address_lines = [line.strip() for line in cleaned_address.split('\n') if line.strip()]
            final_address = ' '.join(address_lines)
            
            return final_address if len(final_address) > 5 else "배송지 정보가 부족합니다"
            
        except Exception as e:
            logger.error(f"배송지 추출 오류: {e}")
            return "배송지 추출 오류"
    
    def validate_results(self, result: ExtractionResult) -> List[str]:
        """추출 결과 검증"""
        warnings = []
        
        if "찾을 수 없습니다" in result.product:
            warnings.append("상품명을 찾지 못했습니다")
        
        if not result.recipient_name or "찾을 수 없습니다" in result.recipient_name:
            warnings.append("수취인명을 찾지 못했습니다")
        
        if not result.contact1 or not self.pm.patterns['phone'].match(result.contact1):
            warnings.append("올바르지 않은 전화번호입니다")
        
        if "찾을 수 없습니다" in result.delivery:
            warnings.append("배송지를 찾지 못했습니다")
        
        return warnings
    
    def process_text(self, text: str, remove_formatting: bool = True) -> ExtractionResult:
        """텍스트 추출 통합 처리"""
        # 서식 제거
        processed_text = self.tp.clean_text_format(text) if remove_formatting else text
        
        # 정보 추출
        product = self.extract_product_info(processed_text)
        options = self.extract_options(processed_text)
        order_quantity = self.extract_order_quantity(processed_text)
        recipient_name, contact1 = self.extract_recipient_info(processed_text)
        delivery = self.extract_delivery_info(processed_text, recipient_name, contact1)
        
        # 서식 제거 적용 (결과에도)
        if remove_formatting:
            product = self.tp.clean_text_format(product)
            options = [self.tp.clean_text_format(opt) for opt in options]
            order_quantity = self.tp.clean_text_format(order_quantity)
            recipient_name = self.tp.clean_text_format(recipient_name)
            contact1 = self.tp.clean_text_format(contact1)
            delivery = self.tp.clean_text_format(delivery)
        
        # 결과 객체 생성
        result = ExtractionResult(
            product=product,
            options=options,
            order_quantity=order_quantity,
            recipient_name=recipient_name,
            contact1=contact1,
            delivery=delivery,
            warnings=[],
            is_valid=True
        )
        
        # 검증
        result.warnings = self.validate_results(result)
        result.is_valid = len(result.warnings) == 0
        
        return result

class UIManager:
    """UI 관리 클래스"""
    
    @staticmethod
    @st.cache_data
    def get_responsive_css() -> str:
        """반응형 CSS 반환 (캐싱 적용)"""
        return """
        <style>
            /* 전체 컨테이너 최적화 */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }
            
            /* 공통 버튼 스타일 */
            .stButton button {
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
                border: none !important;
                border-radius: 25px !important;
                color: white !important;
                font-weight: bold !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
            }
            
            /* 텍스트 영역 최적화 */
            .stTextArea textarea {
                border-radius: 10px !important;
                border: 2px solid #e0e0e0 !important;
                transition: border-color 0.3s ease !important;
            }
            
            .stTextArea textarea:focus {
                border-color: #4ECDC4 !important;
                box-shadow: 0 0 10px rgba(78, 205, 196, 0.3) !important;
            }
            
            /* 모바일 최적화 */
            @media (max-width: 768px) {
                .main .block-container {
                    padding: 1rem 0.5rem !important;
                    max-width: 100% !important;
                }
                
                .stButton button {
                    width: 100% !important;
                    height: 3rem !important;
                    font-size: 18px !important;
                }
                
                .stTextArea textarea {
                    font-size: 16px !important;
                }
                
                h1 { font-size: 24px !important; text-align: center !important; }
                h2, h3 { font-size: 18px !important; }
            }
            
            /* 태블릿 최적화 */
            @media (min-width: 769px) and (max-width: 1024px) {
                .main .block-container {
                    padding: 1.5rem 1rem !important;
                    max-width: 95% !important;
                }
                
                .stButton button {
                    height: 2.5rem !important;
                    font-size: 16px !important;
                }
            }
            
            /* 알림 스타일 */
            .stSuccess { border-radius: 10px !important; border-left: 5px solid #4CAF50 !important; }
            .stWarning { border-radius: 10px !important; border-left: 5px solid #FF9800 !important; }
            .stError { border-radius: 10px !important; border-left: 5px solid #F44336 !important; }
            .stInfo { border-radius: 10px !important; border-left: 5px solid #2196F3 !important; }
        </style>
        """
    
    def apply_responsive_css(self):
        """반응형 CSS 적용"""
        st.markdown(self.get_responsive_css(), unsafe_allow_html=True)
    
    @staticmethod
    def create_copy_section(result: ExtractionResult):
        """복사용 섹션 생성"""
        # 유효한 결과만 필터링
        valid_results = []
        
        if result.product and "찾을 수 없습니다" not in result.product:
            valid_results.append(result.product)
        
        for option in result.options:
            if option and "찾을 수 없습니다" not in option:
                valid_results.append(option)
        
        if result.order_quantity and "찾을 수 없습니다" not in result.order_quantity:
            valid_results.append(result.order_quantity)
        
        if result.recipient_name and "찾을 수 없습니다" not in result.recipient_name:
            valid_results.append(result.recipient_name)
        
        if result.contact1:
            valid_results.append(result.contact1)
        
        if result.delivery and "찾을 수 없습니다" not in result.delivery:
            valid_results.append(result.delivery)
        
        final_text = '\n'.join(valid_results)
        
        # 결과 표시
        st.subheader("📋 추출된 정보")
        st.info("💡 **복사 방법**: 아래 박스 우상단의 복사 버튼을 클릭하거나 텍스트를 선택해서 복사하세요!")
        st.code(final_text, language=None)
        
        return len(valid_results) > 0

def main():
    """메인 애플리케이션"""
    # 페이지 설정
    st.set_page_config(
        page_title="🏪 스마트스토어 주문 정보 추출기",
        page_icon="🏪",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # UI 및 추출기 초기화
    ui_manager = UIManager()
    extractor = OrderExtractor()
    
    # 스타일 적용
    ui_manager.apply_responsive_css()
    
    # 제목
    st.title("🏪 스마트스토어 주문 정보 추출기")
    st.markdown("---")
    
    # 입력 섹션
    st.markdown("### 📝 주문 정보 입력")
    
    text = st.text_area(
        "주문 정보를 붙여넣으세요:",
        height=300,
        placeholder="스마트스토어에서 복사한 주문 정보를 여기에 붙여넣으세요...",
        help="복사한 텍스트를 그대로 붙여넣으면 됩니다"
    )
    
    # 옵션 설정
    col1, col2 = st.columns([3, 1])
    with col1:
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
            try:
                # 정보 추출
                result = extractor.process_text(text, remove_formatting)
                
                # 경고 표시
                if result.warnings:
                    for warning in result.warnings:
                        st.warning(f"⚠️ {warning}")
                
                st.markdown("---")
                
                # 결과 표시
                if ui_manager.create_copy_section(result):
                    st.success("✅ 정보 추출 완료! 위의 복사 버튼을 이용해 정보를 복사하세요.")
                else:
                    st.error("❌ 추출할 수 있는 정보가 없습니다. 원본 텍스트를 확인해주세요.")
                
                # 디버그 정보 (개발용)
                if st.checkbox("🔧 디버그 정보 표시", key="debug"):
                    with st.expander("디버그 정보"):
                        st.json({
                            "product": result.product,
                            "options": result.options,
                            "order_quantity": result.order_quantity,
                            "recipient_name": result.recipient_name,
                            "contact1": result.contact1,
                            "delivery": result.delivery,
                            "warnings": result.warnings,
                            "is_valid": result.is_valid
                        })
                        
                        # 패턴 매칭 디버그
                        st.subheader("패턴 매칭 결과")
                        processed_text = extractor.tp.clean_text_format(text) if remove_formatting else text
                        delivery_match = extractor.pm.patterns['delivery'].search(processed_text)
                        delivery_alt_match = extractor.pm.patterns['delivery_alt'].search(processed_text)
                        
                        st.write("배송지 패턴 1 (배송메모까지):", "✅ 매칭됨" if delivery_match else "❌ 매칭 안됨")
                        if delivery_match:
                            st.code(f"매칭 결과: {delivery_match.group(1)[:200]}...")
                        
                        st.write("배송지 패턴 2 (대체):", "✅ 매칭됨" if delivery_alt_match else "❌ 매칭 안됨")
                        if delivery_alt_match:
                            st.code(f"매칭 결과: {delivery_alt_match.group(1)[:200]}...")
                        
                        # 원본 텍스트 일부 표시
                        st.subheader("처리된 텍스트 (일부)")
                        st.text_area("처리된 텍스트", processed_text[:1000] + "..." if len(processed_text) > 1000 else processed_text, height=200)
                
            except Exception as e:
                logger.error(f"처리 중 오류 발생: {e}")
                st.error(f"❌ 처리 중 오류가 발생했습니다: {str(e)}")
    
    # 사용법 안내
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
        
        ### 🚀 성능 개선사항
        - **캐싱 적용**: 반복 처리 시 더 빠른 속도
        - **메모리 최적화**: 대용량 텍스트 처리 개선
        - **에러 핸들링**: 더 안정적인 동작
        - **코드 구조화**: 유지보수성 향상
        """)

if __name__ == "__main__":
    main()
