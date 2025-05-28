import streamlit as st
import re

def escape_for_js(text):
    """JavaScript에서 사용할 수 있도록 텍스트를 escape 처리"""
    if not text:
        return ""
    # 백틱만 escape 처리 (줄바꿈은 그대로 유지)
    return text.replace('`', '\\`')

def clean_text_format(text):
    """JavaScript에서 사용할 수 있도록 텍스트를 escape 처리"""
    if not text:
        return ""
    return text.replace('`', '\\`').replace('\n', '\\n').replace('\r', '\\r').replace('\\', '\\\\')
    """애플 메일이나 다른 앱에서 복사한 텍스트의 서식을 제거"""
    if not text:
        return text
    
    # 일반적인 서식 문자들 제거
    cleaned = text.replace('\u00a0', ' ')  # Non-breaking space
    cleaned = cleaned.replace('\u2009', ' ')  # Thin space
    cleaned = cleaned.replace('\u200b', '')   # Zero-width space
    cleaned = cleaned.replace('\u200c', '')   # Zero-width non-joiner
    cleaned = cleaned.replace('\u200d', '')   # Zero-width joiner
    cleaned = cleaned.replace('\ufeff', '')   # Byte order mark
    
    # 여러 줄바꿈을 하나로
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    
    # 여러 공백을 하나로
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    # 앞뒤 공백 제거
    cleaned = cleaned.strip()
    
    return cleaned

def extract_product_info(text):
    product_pattern = re.compile(r'상품명(.*?)상품주문상태', re.DOTALL)
    product_match = product_pattern.search(text)
    return product_match.group(1).strip() if product_match else "상품명 및 주문 상태를 찾을 수 없습니다."

def extract_option_order_quantity(text):
    pattern = re.compile(r'옵션(.*?)주문수량', re.DOTALL)
    matches = pattern.findall(text)
    return matches if matches else ["옵션과 주문수량 사이의 텍스트를 찾을 수 없습니다."]

def extract_order_quantity_amount(text):
    pattern = re.compile(r'주문수량\s*([0-9,]+)', re.DOTALL)
    match = pattern.search(text)
    if match:
        return f"주문수량 : {match.group(1).replace(',', '')}"
    else:
        return "주문수량에 해당하는 숫자를 찾을 수 없습니다."

def extract_recipient_info(text):
    recipient_info_pattern = re.compile(r'수취인명(.*?)연락처1(.*?)연락처2', re.DOTALL)
    recipient_info_match = recipient_info_pattern.search(text)
    if recipient_info_match:
        recipient_info_result = recipient_info_match.group(1).strip()
        contact1_result = recipient_info_match.group(2).strip()
        return recipient_info_result, contact1_result
    else:
        return "수취인명, 연락처1, 연락처2를 찾을 수 없습니다.", ""

def extract_delivery_info(text, recipient_info_result, contact1_result):
    # 배송지 주소만 직접 추출
    delivery_address_pattern = re.compile(r'배송지([가-힣\s\d\-\(\),\.]+)\s*배송메모', re.DOTALL)
    delivery_address_match = delivery_address_pattern.search(text)
    
    if delivery_address_match:
        address = delivery_address_match.group(1).strip()
        
        # 배송지에서만 불필요한 시스템 텍스트들 제거 (수취인명은 건드리지 않음)
        # 수취인명과 연락처 정보를 먼저 제거
        if recipient_info_result and recipient_info_result != "수취인명, 연락처1, 연락처2를 찾을 수 없습니다.":
            address = address.replace(recipient_info_result, '')
        if contact1_result:
            address = address.replace(contact1_result, '')
            
        # 시스템 관련 텍스트만 제거 (일반적인 단어는 보존)
        system_texts = [
            '배송지 정보', '수취인명', '연락처1', '연락처2', 
            '배송지', '\t', '\n'
        ]
        
        for system_text in system_texts:
            address = address.replace(system_text, ' ')
        
        # 여러 공백을 하나로 변경하고 앞뒤 공백 제거
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    else:
        return "배송지를 찾을 수 없습니다."

def main():
    st.title("스마트스토어 주문 주소 복사")
    
    # 서식 제거 옵션 추가
    remove_formatting = st.checkbox("서식 제거 (애플 메일 등에서 복사한 경우 체크)", value=True)
    
    text = st.text_area("Enter text here:", height=300)
    
    if st.button("Extract Information"):
        # 서식 제거 옵션이 체크되어 있으면 텍스트 정리
        processed_text = clean_text_format(text) if remove_formatting else text
        
        product_result = extract_product_info(processed_text)
        option_order_quantity_results = extract_option_order_quantity(processed_text)
        order_quantity_numbers = extract_order_quantity_amount(processed_text)
        recipient_info_result, contact1_result = extract_recipient_info(processed_text)
        delivery_info_result = extract_delivery_info(processed_text, recipient_info_result, contact1_result)
        
        # 결과들도 서식 제거
        if remove_formatting:
            product_result = clean_text_format(product_result)
            option_order_quantity_results = [clean_text_format(result) for result in option_order_quantity_results]
            order_quantity_numbers = clean_text_format(order_quantity_numbers)
            recipient_info_result = clean_text_format(recipient_info_result)
            contact1_result = clean_text_format(contact1_result)
            delivery_info_result = clean_text_format(delivery_info_result)
        
        # 개별 결과 표시
        st.subheader("추출된 정보:")
        st.text(product_result)

        for result in option_order_quantity_results:
            st.text(result)

        st.text(order_quantity_numbers)       
        st.text(recipient_info_result)
        st.text(contact1_result)
        st.text(delivery_info_result)
        
        # 복사하기 쉽게 전체 결과를 하나의 텍스트로 제공
        st.subheader("복사용 전체 텍스트:")
        all_results = [
            product_result,
            *option_order_quantity_results,
            order_quantity_numbers,
            recipient_info_result,
            contact1_result,
            delivery_info_result
        ]
        
        # 빈 결과 제거
        filtered_results = [result for result in all_results if result and not result.startswith("찾을 수 없습니다")]
        
        final_text = '\n'.join(filtered_results)
        
        # 복사용 텍스트 영역 (사용자가 직접 전체 선택해서 복사)
        st.text_area(
            "아래 텍스트를 전체 선택(Ctrl+A 또는 Cmd+A)해서 복사하세요:",
            value=final_text,
            height=200,
            key="copy_text",
            help="텍스트 영역을 클릭한 후 Ctrl+A(또는 Cmd+A)로 전체 선택하고 Ctrl+C(또는 Cmd+C)로 복사하세요"
        )
        
        # 추가 정보 표시
        st.info("💡 복사 방법: 위 텍스트 영역을 클릭 → 전체 선택(Ctrl+A) → 복사(Ctrl+C)")
        
        # 개별 정보도 복사하기 쉽게 표시
        st.subheader("개별 정보 복사:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_area("상품명:", value=product_result, height=60, key="product_copy")
            st.text_area("수취인 정보:", value=f"{recipient_info_result}\n{contact1_result}", height=80, key="recipient_copy")
        
        with col2:
            option_text = '\n'.join(option_order_quantity_results) + '\n' + order_quantity_numbers
            st.text_area("옵션 및 수량:", value=option_text, height=80, key="option_copy")
            st.text_area("배송지:", value=delivery_info_result, height=60, key="delivery_copy")

if __name__ == "__main__":
    st.set_page_config(page_title="Order Information Extractor", layout="wide")
    main()
