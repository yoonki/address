import streamlit as st
import re

def extract_product_info(text):
    pattern = r'상품명(.*?)상품주문상태'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else "상품명 및 주문 상태를 찾을 수 없습니다."

def extract_recipient_info(text):
    pattern = r'수취인명(.*?)연락처1(.*?)연락처2'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        recipient_info = match.group(1).strip()
        contact1 = match.group(2).strip()
        return recipient_info, contact1
    else:
        return "수취인명, 연락처1, 연락처2를 찾을 수 없습니다.", ""

def extract_delivery_info(text, recipient_info, contact1):
    info_delivery_text = re.sub(f'{recipient_info}.*?{contact1}', '', text, flags=re.DOTALL)
    pattern = r'배송지(.*?)배송메모'
    match = re.search(pattern, info_delivery_text, re.DOTALL)
    if match:
        delivery_info = match.group(1).strip().replace('정보 배송지 정보 수취인명\t\t연락처2\t 배송지', '').strip()
        return delivery_info
    else:
        return "배송지 및 배송메모를 찾을 수 없습니다."

def main():
    st.title("스.스 주소")
    text = st.text_area("Enter text:", height=200)

    if st.button("Extract Information"):
        product_result = extract_product_info(text)
        recipient_info, contact1 = extract_recipient_info(text)
        delivery_info = extract_delivery_info(text, recipient_info, contact1)

        st.text(f"Product Information: {product_result}")
        st.text(f"Recipient Information: {recipient_info} {contact1}")
        st.text(f"Delivery Information: {delivery_info}")

        # Add a line break for easy pasting and searching
        st.text("")

        # Display the text for easy copying
        st.text("Copy and paste the above information for quick search.")

if __name__ == "__main__":
    main()
