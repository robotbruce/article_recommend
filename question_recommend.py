# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 18:53:41 2021

@author: bruceyu1113
"""

import os
import pandas as pd
import jieba_fast as jieba
import numpy as np
import re
#import time
from w3lib.html import remove_tags, replace_entities
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn import preprocessing

def cleaning_content():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    table = pd.read_csv('giver_questions_for_exam.csv')    
#    table = Table.copy()
    #去除html標記和encode標點符號  
    cleaning_content = table['content'].apply(lambda x : ' '.join(remove_tags(replace_entities(x)).split('\n')))
    #將所有英文轉大寫
    cleaning_content = cleaning_content.apply(lambda x : np.char.upper(x))
    #停用字dict
    stopwords = open("stopwords.txt",encoding = 'UTF-8').read().split()
    #jieba斷詞
    jieba_content = cleaning_content.apply(lambda x : [w for w in jieba.lcut_for_search(x) if len(w) > 1 and re.compile(r"[A-Z\u4e00-\u9fa5]").findall(w)])
    jieba_remove = jieba_content.apply(lambda x : [w for w in x if w not in stopwords])
    tag_s1= jieba_remove.apply(lambda x : ' '.join(x))
    
    
# =============================================================================
#    tag_s1 = tag_s1.replace('',np.NAN).dropna()    
    texts = [[word for word in tag_s1.split()] for tag_s1 in tag_s1]
    frequency = defaultdict(int)
    for text in texts:
        for word in text:
            frequency[word]+=1
    texts_top = [i[0] for i in sorted(frequency.items(), key=lambda x:-x[1])[:10000]]
    texts = [[word for word in text if word in texts_top] for text in texts]
    
    table['tag'] = texts

    table['tag'] = [' '.join(map(str, l)) for l in table['tag']]
    table = table.replace(r'^\s*$', np.nan, regex=True)
    table.dropna(axis=0,subset=['tag'],inplace = True)
#    tag_s1 = tag_s1.replace('',np.NAN).dropna()
    table = table.drop(columns=['content'])
#    table.reset_index(inplace=True)
    
#    table['index'] = table['index'].astype(str)
#    table.rename(columns={"index": "new_qid"},inplace = True)
    test_table = table[["question_id","tag"]]
    
    v = TfidfVectorizer()
    x = v.fit_transform(test_table['tag'])
#    df1 = pd.DataFrame(x.toarray(), columns=v.get_feature_names())
    
#    words = v.get_feature_names()
    
    similarity_matrix = cosine_similarity(x, x)
    
    aaa = pd.DataFrame(similarity_matrix,index=table['question_id'],columns=table['question_id'])

    ##找出相關文章前50
    score_dict = {}
    for index, row in aaa.iterrows():
        temp_df = pd.DataFrame(row)
        temp_df = temp_df[temp_df[index] > 0]
        temp_df.sort_values(index,ascending=False,inplace = True)
        temp_df = temp_df.drop(index)
        temp_df = temp_df.head(50)
        temp_list = temp_df.index.tolist()
        temp_list = [str(x) for x in temp_list]
        score_dict.update({index:temp_list})
    return(score_dict)
    
#def Top_Ranking(WEB_LOG,SCORE_DICT):
def Top_Ranking(SCORE_DICT):
#    web_log = WEB_LOG.copy()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    web_log = pd.read_csv('giver_question_behaviors_for_exam.csv')
    ##比對article後臺是否有存在,若不存在則不推薦
    score_dict = SCORE_DICT.copy()
    question_base = pd.DataFrame(score_dict.keys(),columns=["question_id"])
    web_log = web_log[web_log["question_id"].isin(question_base["question_id"])]
    
    #計算question_id之下每個互動行為之分數
#    action = ['view','clap','attention','share','thank']
#    score = web_log[["question_id"]].loc[~web_log[["question_id"]].duplicated(),:]
#    for action_type in action:
#        temp_score = web_log[web_log["event"]==action_type].groupby(["question_id"])['pid'].count().reset_index(name=action_type)
#        score = pd.merge(score,temp_score, on = ['question_id'],how = 'left')
    score = web_log.pivot_table(values="pid", index="question_id", columns="event", aggfunc="count",fill_value=0).reset_index()
    action = list(score.iloc[:,1:].columns)
    question_name = score["question_id"]
#    score = score.fillna(0)
    score.set_index('question_id',inplace=True)
    
    #分數標準化
    x = score.values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    normal_score = pd.DataFrame(x_scaled,index = question_name,columns=action)
    #加權
    score['score'] = normal_score['view']*0.05+normal_score['clap']*0.1+normal_score['attention']*0.3+normal_score['share']*0.3+normal_score['thank']*0.2
    date_last_temp= web_log.sort_values('event_date').drop_duplicates('question_id',keep='last')[["question_id","event_date"]].rename(columns={"event_date": "last_date"}).set_index("question_id")
    score = pd.merge(score,date_last_temp, left_index=True, right_index=True,how = 'left')
    
    score.sort_values("score",ascending=False,inplace = True)
    score_top = score.reset_index()[['question_id']].head(500)["question_id"].tolist()
    return(score_top)

def recommend_article(DICT_SIMILAR,LIST_RANKTOP):
    similar_dict = DICT_SIMILAR.copy()
    ranktop_df = LIST_RANKTOP.copy()
    sc_dict_of_frame={}
    for question_name,similar_article_list in similar_dict.items():
        temp_df = pd.DataFrame(similar_article_list)
        temp_df = temp_df.append(ranktop_df)
        temp_df.columns = ["re_questions"]
        temp_df = temp_df[~temp_df.re_questions.str.contains(question_name)]
        temp_df.drop_duplicates(subset = ["re_questions"],keep = 'first',inplace = True)
        temp_df.reset_index(drop = True,inplace=True)
        test_list = temp_df.head(50)["re_questions"].tolist()
        sc_dict_of_frame.update({question_name:test_list})
    return(sc_dict_of_frame)
    
def user_prefer():
    ##計算user對每篇article互動分數,挑選最高分之文章,若相同則挑選最近互動時間之文章##
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    web_log = pd.read_csv('giver_question_behaviors_for_exam.csv').copy()
    #對每位user計算每天文章偏好分數
    user_active_score = web_log.pivot_table(values="event_date", index=["pid","question_id"], columns="event", aggfunc="count",fill_value=0)
    user_active_score['score'] = user_active_score['view']*0.05+user_active_score['clap']*0.1+user_active_score['attention']*0.3+user_active_score['share']*0.3+user_active_score['thank']*0.2
    #select使用者同一article最後互動時間
    date_select = web_log.groupby(["pid","question_id"],sort=False)["event_date"].max()
    #合併偏好分數與互動時間
    user_active_score = pd.merge(user_active_score,date_select, left_index=True, right_index=True,how = 'left').reset_index()
    user_active_score = user_active_score.sort_values(by=["pid","score","event_date"],ascending=[True,False,False])
    user_active_score.drop_duplicates(subset = ["pid"],keep = 'first',inplace = True)
    user_active_score.reset_index(inplace=True,drop=True)
    return(user_active_score)
    
def user_recomment(DF_USER_PREFER_SCORE,DICT_RECOMMEND_ARTICLE,LIST_ARTICLE_RANK):
    df_users_prefer_score = DF_USER_PREFER_SCORE.copy()
    list_article_rank = LIST_ARTICLE_RANK.copy()
    dict_recommend_article = DICT_RECOMMEND_ARTICLE.copy()
    df_recomment_article = pd.DataFrame(list(dict_recommend_article.items()),columns=["question_id","recommend_article"]) 
    user_recommend = pd.merge(df_users_prefer_score[["pid","question_id"]],df_recomment_article,on = ['question_id'],how = 'left')[["pid","recommend_article"]]
    #若user比對文章比對不到則補上熱門文章
    for row in user_recommend.loc[user_recommend.recommend_article.isnull(), 'recommend_article'].index:
        user_recommend.at[row, 'recommend_article'] = list_article_rank
    return(user_recommend)
    
#if __name__=='__main__':
#    tStart = time.time()
#    os.chdir(os.getcwd())
#    qTable = pd.read_csv('giver_questions_for_exam.csv')
#    log = pd.read_csv('giver_question_behaviors_for_exam.csv')
#    dict_sc = cleaning_content()
#    list_article_rank = Top_Ranking(dict_sc)
#    dict_recommend_article = recommend_article(dict_sc,list_article_rank)
#    df_users_prefer_score = user_prefer()
#    df_user_recommend = user_recomment(df_users_prefer_score,dict_recommend_article,list_article_rank)
#    tEnd = time.time()
#    print ( "  -->  runtime : " + str(round((tEnd - tStart)/60,2)) + ' min')

