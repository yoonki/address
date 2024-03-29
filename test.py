import streamlit as st
import re

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
    text = st.text_area("Enter text here:", height=300)  # Added height for better usability
    
    if st.button("Extract Information"):
        product_result = extract_product_info(text)
        option_order_quantity_results = extract_option_order_quantity(text)
        order_quantity_numbers =extract_order_quantity_amount(text)
        recipient_info_result, contact1_result = extract_recipient_info(text)
        delivery_info_result = extract_delivery_info(text, recipient_info_result, contact1_result)
        
        # st.subheader("Product Information:")
        st.text(product_result)

        # st.subheader("Option and Order Quantity Information:")
        for result in option_order_quantity_results:
            st.text(result)

        st.text(order_quantity_numbers)       
        # st.subheader("Recipient Information:")
        st.text(recipient_info_result)
        st.text(contact1_result)

        # st.subheader("Delivery Information:")
        st.text(delivery_info_result)

if __name__ == "__main__":
    st.set_page_config(page_title="Order Information Extractor", layout="wide")
    main()

