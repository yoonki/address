import re
import streamlit as st

form = st.form(key="submit-form")
input_text = re.sub(r"수취인명|연락처.|배송지|정보|배송메모|배송구분|국내배송|수령자명|수령자정보수정|..전화|주소|수정|--", ",", form.text_input("네이버 배송주소를 복사에서 입력 하세요"))
input_text = input_text.replace('\t\t','').replace('\t','\n').replace('\n,\n','\n').replace(',','').replace('\n \n','\n')
generate = form.form_submit_button("Generate")
st.text(input_text)
