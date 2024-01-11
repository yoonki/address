import streamlit as st
import re

def extract_product_info(text):
    product_pattern = re.compile(r'상품명(.*?)상품주문상태', re.DOTALL)
    product_match = product_pattern.search(text)
    return product_match.group(1).strip() if product_match else "상품명 및 주문 상태를 찾을 수 없습니다."

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
    info_delivery_text = re.sub(f'{recipient_info_result}.*?{contact1_result}', '', text, flags=re.DOTALL)
    delivery_info_pattern = re.compile(r'배송지(.*?)배송메모', re.DOTALL)
    delivery_info_match = delivery_info_pattern.search(info_delivery_text)
    if delivery_info_match:
        delivery_info_result = delivery_info_match.group(1).strip()
        return delivery_info_result.replace('정보 배송지 정보 수취인명\t\t연락처2\t 배송지','').strip()
    else:
        return "배송지 및 배송메모를 찾을 수 없습니다."

def main():
    st.title("스마트스토어 주문 주소 복사")
    text = st.text_area("Enter text:")
    
    if st.button("Extract Information"):
        product_result = extract_product_info(text)
        recipient_info_result, contact1_result = extract_recipient_info(text)
        delivery_info_result = extract_delivery_info(text, recipient_info_result, contact1_result)

        st.text(product_result)


        st.text(recipient_info_result)
        st.text(contact1_result)


        st.text(delivery_info_result)

if __name__ == "__main__":
    main()
