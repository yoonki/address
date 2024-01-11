import re
import streamlit as st

def extract_information(text):
    # 정규식 패턴 설정
    product_pattern = re.compile(r'상품명(.*?)상품주문상태', re.DOTALL)
    recipient_info_pattern = re.compile(r'수취인명(.*?)연락처1(.*?)연락처2', re.DOTALL)
    delivery_info_pattern = re.compile(r'배송지(.*?)배송메모', re.DOTALL)

    # 상품명과 상품주문상태 사이의 문자열 찾기
    product_match = product_pattern.search(text)
    if product_match:
        product_result = product_match.group(1).strip()
    else:
        product_result = "상품명 및 주문 상태를 찾을 수 없습니다."

    # 수취인명과 연락처1, 연락처2 사이의 문자열 찾기
    recipient_info_match = recipient_info_pattern.search(text)
    if recipient_info_match:
        recipient_info_result = recipient_info_match.group(1).strip()
        contact1_result = recipient_info_match.group(2).strip()
    else:
        recipient_info_result = "수취인명, 연락처1, 연락처2를 찾을 수 없습니다."
        contact1_result = ""

    # 정보와 배송지 사이의 문자열 삭제
    info_delivery_text = re.sub(f'{recipient_info_result}.*?{contact1_result}', '', text, flags=re.DOTALL)

    # 배송지와 배송메모 사이의 문자열 찾기
    delivery_info_match = delivery_info_pattern.search(info_delivery_text)
    if delivery_info_match:
        delivery_info_result = delivery_info_match.group(1).strip()
    else:
        delivery_info_result = "배송지 및 배송메모를 찾을 수 없습니다."

    return product_result, recipient_info_result, contact1_result, delivery_info_result


# Streamlit app
def main():
    st.title("Text Information Extractor")

    # Text input
    text = st.text_area("Input Text", "")

    # Button to extract information
    if st.button("Extract Information"):
        product_result, recipient_info_result, contact1_result, delivery_info_result = extract_information(text)

        # Display results
        st.write(product_result)

        st.write(recipient_info_result)
        st.write(contact1_result)

        st.write(delivery_info_result.replace('정보 배송지 정보 수취인명\t\t연락처2\t 배송지', '').strip())


if __name__ == "__main__":
    main()
