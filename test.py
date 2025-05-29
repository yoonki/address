import gradio as gr
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
        return f"추출 중 오류 발생 ({pattern_key}): {str(e)}"

def extract_product_info(text):
    """상품 정보 추출"""
    return extract_between_patterns(text, 'product', "상품명을 찾을 수 없습니다")

def extract_option_order_quantity(text):
    """옵션 정보 추출"""
    try:
        matches = PATTERNS['option'].findall(text)
        return matches if matches else ["옵션 정보를 찾을 수 없습니다"]
    except Exception as e:
        return [f"옵션 추출 중 오류: {str(e)}"]

def extract_order_quantity_amount(text):
    """주문수량 추출"""
    try:
        match = PATTERNS['order_quantity'].search(text)
        if match:
            return f"주문수량 : {match.group(1).replace(',', '')}"
        return "주문수량을 찾을 수 없습니다"
    except Exception as e:
        return f"주문수량 추출 중 오류: {str(e)}"

def extract_recipient_info(text):
    """수취인 정보 추출"""
    try:
        match = PATTERNS['recipient'].search(text)
        if match:
            recipient_name = match.group(1).strip()
            contact1 = match.group(2).strip()
            return recipient_name, contact1
        return "수취인 정보를 찾을 수 없습니다", ""
    except Exception as e:
        return f"수취인 정보 추출 오류: {str(e)}", ""

def clean_address_text(address, recipient_name, contact1):
    """주소 텍스트 정리 (최적화된 버전)"""
    # 수취인 정보 제거
    if recipient_name and "찾을 수 없습니다" not in recipient_name:
        address = address.replace(recipient_name, '')
    if contact1:
        address = address.replace(contact1, '')
    
    # 시스템 키워드들을 한 번에 제거
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
        return f"배송지 추출 중 오류: {str(e)}"

def validate_extraction_results(results):
    """추출 결과 검증"""
    warnings = []
    
    if "찾을 수 없습니다" in results.get('product', ''):
        warnings.append("⚠️ 상품명을 찾지 못했습니다")
    
    if not results.get('recipient_name') or "찾을 수 없습니다" in results['recipient_name']:
        warnings.append("⚠️ 수취인명을 찾지 못했습니다")
    
    if not results.get('contact1') or not PATTERNS['phone'].match(results['contact1']):
        warnings.append("⚠️ 올바르지 않은 전화번호입니다")
    
    if "찾을 수 없습니다" in results.get('delivery', ''):
        warnings.append("⚠️ 배송지를 찾지 못했습니다")
    
    return warnings

def process_smartstore_text(text, remove_formatting=True):
    """스마트스토어 텍스트 처리 메인 함수"""
    if not text or not text.strip():
        return "❌ 텍스트를 입력해주세요!", []
    
    try:
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
        
        # 최종 결과 텍스트 생성
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
            if result and not any(error in result for error in ["찾을 수 없습니다", "오류", "부족합니다"])
        ]
        
        if not filtered_results:
            return "❌ 추출할 수 있는 유효한 정보가 없습니다.", []
        
        final_text = '\n'.join(filtered_results)
        
        # 검증 및 경고 메시지
        warnings = validate_extraction_results(results)
        warning_text = '\n'.join(warnings) if warnings else ""
        
        # 성공 메시지와 함께 결과 반환
        success_msg = "✅ 정보 추출 완료!"
        if warning_text:
            success_msg += f"\n\n{warning_text}"
        
        return success_msg, final_text
        
    except Exception as e:
        return f"❌ 처리 중 오류가 발생했습니다: {str(e)}", ""

def create_interface():
    """Gradio 인터페이스 생성"""
    
    # CSS 스타일링
    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .input-container, .output-container {
        border-radius: 10px !important;
    }
    .gr-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
        border: none !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        color: white !important;
    }
    .gr-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
    }
    """
    
    with gr.Blocks(
        title="🏪 스마트스토어 주문 정보 추출기",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="green",
            neutral_hue="gray"
        ),
        css=custom_css
    ) as demo:
        
        # 헤더
        gr.Markdown("""
        # 🏪 스마트스토어 주문 정보 추출기
        
        스마트스토어에서 복사한 주문 정보를 붙여넣으면 필요한 정보만 깔끔하게 정리해드립니다!
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 입력 영역
                gr.Markdown("### 📝 주문 정보 입력")
                
                input_text = gr.Textbox(
                    label="주문 정보를 붙여넣으세요",
                    placeholder="스마트스토어에서 복사한 주문 정보를 여기에 붙여넣으세요...",
                    lines=15,
                    max_lines=20
                )
                
                with gr.Row():
                    remove_format_checkbox = gr.Checkbox(
                        label="서식 자동 제거",
                        value=True,
                        info="애플 메일 등에서 복사한 텍스트의 서식을 자동으로 제거합니다"
                    )
                    
                    extract_btn = gr.Button(
                        "🔍 정보 추출하기",
                        variant="primary",
                        size="lg"
                    )
            
            with gr.Column(scale=1):
                # 상태 및 도움말
                gr.Markdown("### ℹ️ 사용법")
                gr.Markdown("""
                1. **스마트스토어**에서 주문 정보를 복사
                2. 왼쪽 텍스트 박스에 **붙여넣기**
                3. **🔍 정보 추출하기** 버튼 클릭
                4. 추출된 정보를 **복사**해서 사용
                
                ✨ **자동으로 추출되는 정보:**
                - 상품명
                - 옵션 정보
                - 주문수량
                - 수취인명
                - 연락처
                - 배송지 주소
                """)
        
        # 결과 영역
        gr.Markdown("---")
        gr.Markdown("### 📋 추출 결과")
        
        with gr.Row():
            status_output = gr.Textbox(
                label="상태",
                interactive=False,
                lines=3
            )
        
        with gr.Row():
            result_output = gr.Code(
                label="추출된 정보 (복사 버튼 사용)",
                language=None,
                interactive=False,
                lines=10
            )
        
        # 이벤트 연결
        extract_btn.click(
            fn=process_smartstore_text,
            inputs=[input_text, remove_format_checkbox],
            outputs=[status_output, result_output]
        )
        
        # 엔터 키로도 실행 가능
        input_text.submit(
            fn=process_smartstore_text,
            inputs=[input_text, remove_format_checkbox],
            outputs=[status_output, result_output]
        )
        
        # 푸터
        gr.Markdown("""
        ---
        
        💡 **팁**: 추출된 정보 박스 우상단의 복사 버튼을 클릭하면 쉽게 복사할 수 있습니다!
        
        🛠️ **문제가 있다면**: 텍스트를 다시 확인하거나 '서식 자동 제거' 옵션을 체크해보세요.
        """)
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",  # 외부 접속 허용
        server_port=7860,       # 포트 설정
        share=False,            # Gradio 공유 링크 (필요시 True)
        show_error=True,        # 에러 표시
        quiet=False             # 로그 표시
    )
