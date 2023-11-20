import streamlit as st
from numpy.lib.function_base import select
import requests
from bs4 import BeautifulSoup
import json
import datetime
import pandas as pd
import urllib3
from urllib.request import urlopen
import urllib.request
import ssl
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer


pd.options.display.max_rows = 1000

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

today = datetime.datetime.today().strftime("%Y%m%d_%H%M")  
search = st.text_input('검색어 입력')

query = urllib.parse.quote(search)
sort = {'네이버랭킹순' : 'rel', 
        '낮은가격순' : 'price_asc', 
        '리뷰많은순' : 'review'    
}

url = 'https://search.shopping.naver.com/search/all?frm=NVSHATC&origQuery=' + query + '&pagingIndex=' + '1' + '&pagingSize=80&productSet=total&query=' + query +'&sort=' +str(sort['네이버랭킹순']) +'&timestamp=&viewType=list#' 

response = requests.get(url, verify=False)
html = response.text
soup = BeautifulSoup(html, 'html.parser')
script = soup.select_one('#__NEXT_DATA__')  

value = ''
for i in script:
    startPoint = i.find('{')
    jsonData = i[startPoint :len(i)]
    value = json.loads(jsonData)
items = value['props']['pageProps']['initialState']['products']['list']
try : 
    relatedTags = value['props']['pageProps']['initialState']['relatedTags']
    relatedTag = pd.DataFrame(relatedTags)
    #relatedTag.to_csv(today + search+'_연관검색어.csv', encoding="utf-8-sig")
except :
    pass

idx = 0
shop_df = pd.DataFrame(columns=("랭킹", "스토어명", "제품이름", "최저가", "모바일최저가", '구매포인트','쿠폰', '이벤트','구매건수', '리뷰수','검색태그','속성' , "링크"))
for i in range(len(items)):
    rank = items[i]['item']['rank']
    try :
        mallName = items[i]['item']['mallName']
    except :
        mallName = '상점이름 없음'
    productName = items[i]['item']['productName'].upper()
    lowPrice = items[i]['item']['lowPrice']
    mobileLowPrice = items[i]['item']['mobileLowPrice']
    buyPointContent = items[i]['item']['buyPointContent'].split('^')[1]
    try : 
        eventContent = items[i]['item']['eventContent']
    except :
        eventContent = '이벤트없음'

    couponContent=items[i]['item']['couponContent'].split('^')[3]
    purchaseCnt = items[i]['item']['purchaseCnt']
    try : 
        mallProductUrl = items[i]['item']['mallProductUrl']
    except : 
        mallProductUrl = '광고'
    try : 
        manuTag = items[i]['item']['manuTag']
    except :
        manuTag = '태그 없음'
    try:
        characterValue = items[i]['item']['characterValue']
    except :
        characterValue = '속성값 없음'
    reviewCountSum = items[i]['item']['reviewCountSum']
    shop_df.loc[idx]= [rank, mallName, productName, lowPrice, mobileLowPrice, buyPointContent, couponContent, eventContent, purchaseCnt, reviewCountSum, manuTag, characterValue, mallProductUrl]
    idx += 1

shop_df['최저가'] = pd.to_numeric(shop_df['최저가']).fillna(0).astype(int)
shop_df['모바일최저가'] = pd.to_numeric(shop_df['모바일최저가']).fillna(0).astype(int)
shop_df['구매포인트'] = pd.to_numeric(shop_df['구매포인트']).fillna(0).astype(int)
shop_df['쿠폰'] = pd.to_numeric(shop_df['쿠폰']).fillna(0).astype(int)
# shop_df.to_csv(today + search+'.csv', encoding="utf-8-sig")
신고 = shop_df[["랭킹", "스토어명", "제품이름", "최저가", "모바일최저가", '구매포인트','쿠폰', '이벤트','구매건수', '리뷰수',"링크"]]
# 신고.to_csv(today + search+'.csv', encoding="utf-8-sig")
st.write(url)
productNames = shop_df.get('제품이름')
manuTag = shop_df.get('검색태그')
characterValue = shop_df.get('속성')


def freq_word(min, range, vector):
    vectorizer = CountVectorizer(analyzer= 'word', tokenizer= None, preprocessor= None, stop_words= None, min_df= min, ngram_range=(1, range), max_features= 2000, lowercase=False)
    feature_vector = vectorizer.fit_transform(vector)
    vocab = vectorizer.get_feature_names_out()
    dist = np.sum(feature_vector, axis=0)
    df_freq = pd.DataFrame(dist, columns=vocab)
    freq = pd.DataFrame(df_freq.T.sort_values(by=0, ascending=False))
    return freq

# 단어빈도 가중치
vectorizer = CountVectorizer(analyzer= 'word', tokenizer= None, preprocessor= None, stop_words= None, min_df= 2, ngram_range=(1, 1), max_features= 2000, lowercase=False)
feature_vector = vectorizer.fit_transform(productNames)
vocab = vectorizer.get_feature_names_out()
transformer =TfidfTransformer(smooth_idf=False)
feature_tfidf = transformer.fit_transform(feature_vector)
tfidf_freq = pd.DataFrame(feature_tfidf.toarray(), columns=vocab)
df_tfidf = pd.DataFrame(tfidf_freq.sum())
soft_df_tfidf = df_tfidf.sort_values(by=0, ascending=False)


df = shop_df.set_index('스토어명')

csv_df = shop_df[['스토어명','제품이름', '최저가', '모바일최저가','링크']]

# print(url)
df_link = df[df['링크'].str.contains("smart")]
test_link = np.array(df_link.링크.tolist())
url = test_link[0]

q1 = shop_df['모바일최저가'].quantile(0.25)
# shop_df.to_csv(f'{today} {search}.csv', encoding="utf-8-sig")
shop_df['구매건수'] = pd.to_numeric(shop_df['구매건수'])
shop_df['리뷰수'] = pd.to_numeric(shop_df['리뷰수'])

st.write(f'검색어 : {search}')
st.write('6개월판매수량 : '+str(shop_df['구매건수'].sum()))
st.write('리뷰수 : '+str(shop_df['리뷰수'].sum()))
st.dataframe(shop_df)
st.dataframe(freq_word(1, 1, productNames))
st.dataframe(freq_word(1, 1, manuTag))
