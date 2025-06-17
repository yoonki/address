import streamlit as st
import re

class OrderExtractor:
    """간소화된 주문 정보 추출 클래스"""
    
    def __init__(self):
        # 정규표현식 패턴들
        self.patterns = {
            'product': re.compile(r'상품명\s*(.*?)\s*상품주문상태', re.DOTALL),
            'option': re.compile(r'옵션\s*(.*?)\s*주문수량', re.DOTALL),
            'order_quantity': re.compile(r'주문수량\s*([0-9,]+)', re.DOTALL),
            'recipient_with_contact2': re.compile(r'수취인명[\s\t]*(.*?)[\s\t]*연락처1[\s\t]*(.*?)[\s\t]*연락처2[\s\t]*(.*?)[\s\t]*배송지', re.DOTALL),
            'recipient_no_contact2': re.compile(r'수취인명[\s\t]*(.*?)[\s\t]*연락처1[\s\t]*(.*?)[\s\t]*배송지', re.DOTALL),
            'delivery': re.compile(r'배송지[\s\t]+(.*?)[\s\t]*배송메모', re.DOTALL),
            'delivery_alt': re.compile(r'배송지[\s\t]*([^\n\t]+(?:\n[^\t\n]+)*)', re.DOTALL),
            'delivery_memo': re.compile(r'배송메모[\s\t]*([^\n\r]+)', re.DOTALL),
        }
    
    def clean_text(self, text):
        """텍스트 정리"""
        if not text:
            return ""
        
        # 특수문자 제거 및 공백 정리
        text = text.replace('\t', ' ').replace('\u00a0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_info(self, text):
        """모든 정보 추출"""
        text = self.clean_text(text)
        result = {}
        
        # 상품명 추출
        match = self.patterns['product'].search(text)
        result['product'] = self.clean_text(match.group(1)) if match else ""
        
        # 옵션 추출
        match = self.patterns['option'].search(text)
        result['option'] = self.clean_text(match.group(1)) if match else ""
        
        # 주문수량 추출
        match = self.patterns['order_quantity'].search(text)
        result['quantity'] = f"주문수량 : {match.group(1)}" if match else ""
        
        # 수취인 정보 추출 (연락처2 있는 경우 먼저 시도)
        match = self.patterns['recipient_with_contact2'].search(text)
        if match:
            result['recipient'] = self.clean_text(match.group(1))
            result['contact1'] = self.clean_text(match.group(2))
            result['contact2'] = self.clean_text(match.group(3))
        else:
            # 연락처2 없는 경우
            match = self.patterns['recipient_no_contact2'].search(text)
            if match:
                result['recipient'] = self.clean_text(match.group(1))
                result['contact1'] = self.clean_text(match.group(2))
                result['contact2'] = ""
            else:
                result['recipient'] = ""
                result['contact1'] = ""
                result['contact2'] = ""
        
        # 배송지 추출
        match = self.patterns['delivery'].search(text)
        if match:
            delivery_text = match.group(1)
        else:
            match = self.patterns['delivery_alt'].search(text)
            delivery_text = match.group(1) if match else ""
        
        if delivery_text:
            # 배송지에서 수취인 정보 제거
            for info in [result['recipient'], result['contact1'], result['contact2']]:
                if info:
                    delivery_text = delivery_text.replace(info, '')
            
            # 불필요한 키워드 제거
            for keyword in ['정보', '배송지 정보', '수취인명', '연락처1', '연락처2', '배송지']:
                delivery_text = delivery_text.replace(keyword, '')
            
            # 줄바꿈 정리
            lines = [line.strip() for line in delivery_text.split('\n') if line.strip()]
            result['delivery'] = '\n'.join(lines)
        else:
            result['delivery'] = ""
        
        # 배송메모 추출
        match = self.patterns['delivery_memo'].search(text)
        if match:
            memo = self.clean_text(match.group(1))
            # 불필요한 정보 제거
            unwanted = ['주문 처리 이력', '처리일', '주문', '결제완료', '닫기', '정보', '발주확인', '발송기한']
            for word in unwanted:
                memo = memo.replace(word, '')
            # 날짜 패턴 제거
            memo = re.sub(r'\d{4}[.-]?\d{2}[.-]?\d{2}', '', memo)
            memo = re.sub(r'\d{2}:\d{2}:\d{2}', '', memo)
            # 시간 패턴과 콜론, 하이픈 제거
            memo = re.sub(r'\d{2}:\d{2}:\d{2}', '', memo)
            memo = re.sub(r'[:\-\s]+', ' ', memo).strip()
            # 배송메모가 실제로 의미있는 내용이 있는지 확인
            result['delivery_memo'] = memo if len(memo) > 2 and not memo.isdigit() and memo.strip() else ""
        else:
            result['delivery_memo'] = ""
        
        return result
    
    def format_output(self, result):
        """출력 형식으로 포맷팅"""
        output_lines = []
        
        # 각 정보를 순서대로 추가 (값이 있는 경우만)
        if result['product']:
            output_lines.append(result['product'])
        
        if result['option']:
            output_lines.append(result['option'])
        
        if result['quantity']:
            output_lines.append(result['quantity'])
        
        if result['recipient']:
            output_lines.append(result['recipient'])
        
        if result['contact1']:
            output_lines.append(result['contact1'])
        
        if result['contact2']:
            output_lines.append(result['contact2'])
        
        if result['delivery']:
            output_lines.append(result['delivery'])
        
        if result['delivery_memo']:
            output_lines.append(f"배송메모: {result['delivery_memo']}")
        
        return '\n'.join(output_lines)

def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="🏪 스마트스토어 주문 정보 추출기",
        page_icon="🏪",
        layout="wide"
    )
    
    # 간단한 CSS
    st.markdown("""
    <style>
        .stButton button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
            border: none !important;
            border-radius: 25px !important;
            color: white !important;
            font-weight: bold !important;
        }
        .stTextArea textarea {
            border-radius: 10px !important;
            border: 2px solid #e0e0e0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 제목
    st.title("🏪 스마트스토어 주문 정보 추출기")
    st.markdown("---")
    
    # 추출기 초기화
    extractor = OrderExtractor()
    
    # 입력 섹션
    st.markdown("### 📝 주문 정보 입력")
    text = st.text_area(
        "주문 정보를 붙여넣으세요:",
        height=300,
        placeholder="스마트스토어에서 복사한 주문 정보를 여기에 붙여넣으세요..."
    )
    
    # 처리 버튼
    if st.button("🔍 정보 추출하기", type="primary", use_container_width=True):
        if not text.strip():
            st.error("📝 텍스트를 입력해주세요!")
            return
        
        with st.spinner("🔄 정보를 추출하는 중..."):
            try:
                # 정보 추출
                result = extractor.extract_info(text)
                formatted_output = extractor.format_output(result)
                
                if formatted_output:
                    st.markdown("---")
                    st.subheader("📋 추출된 정보")
                    st.info("💡 **복사 방법**: 아래 박스 우상단의 복사 버튼을 클릭하거나 텍스트를 선택해서 복사하세요!")
                    st.code(formatted_output, language=None)
                    st.success("✅ 정보 추출 완료!")
                else:
                    st.error("❌ 추출할 수 있는 정보가 없습니다. 원본 텍스트를 확인해주세요.")
                
                # 디버그 정보
                if st.checkbox("🔧 디버그 정보 표시"):
                    with st.expander("디버그 정보"):
                        st.json(result)
                
            except Exception as e:
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
        - 📞 연락처1, 연락처2 (있는 경우)
        - 🏠 배송지 주소 (줄바꿈 유지)
        - 📝 배송메모 (있는 경우)
        
        ### 💡 팁
        - 복사 버튼이 안 보이면 텍스트를 직접 선택해서 복사하세요
        - 정보가 제대로 추출되지 않으면 원본 텍스트를 다시 확인해보세요
        - 연락처2가 있으면 자동으로 별도 줄에 표시됩니다
        """)

if __name__ == "__main__":
    main()
