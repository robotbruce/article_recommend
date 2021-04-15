# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 09:45:35 2021

@author: bruceyu1113
"""
import sys
import requests
import os
import pandas as pd
from flask import Blueprint,request,jsonify
from datetime import datetime
path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, path)
from cache import cache
import question_recommend as qr
from df_to_json import dataframe_to_json

##宣告Blueprint route名稱##
recommend_api = Blueprint('recommend_api',__name__,url_prefix='/recommend_api')
##

@recommend_api.route('/getdata')
def getdata():
    return{'news': 'value'}
# =============================================================================

@recommend_api.route('/content_clear', methods=['GET'])##News 標籤推薦API   
def content_clear():
    hour = datetime.now().hour
    minute = datetime.now().minute
    content_cache = cache.get('content_cache')
    try:
        if (not content_cache) or \
        ((hour>9 and minute > 0) and (hour>9 and minute <= 2)):
            print('Not cache')
            dict_sc = qr.cleaning_content() 
            json_dict_sc = jsonify(dict_sc)
            json_dict_sc.status_code=200
            cache.set('content_cache',json_dict_sc,timeout=86400)
            return(json_dict_sc)
        else:
            print('content_cache')
            return content_cache
    finally:
        print('request get /content_clear')
        
@recommend_api.route('/top_rank', methods=['GET'])##News 標籤推薦API   
def top_rank():
    hour = datetime.now().hour
    minute = datetime.now().minute
    top_rank_cache = cache.get('top_rank')
    try:
        if (not top_rank_cache) or \
        ((hour>9 and minute > 0) and (hour>9 and minute <= 2)):
            print('Not cache')
            content = requests.get(f"http://127.0.0.1:8010/recommend_api/content_clear")
            content = content.json()
            top_rank = qr.Top_Ranking(content)
            json_top_rank = jsonify({"top_rank":top_rank})
            json_top_rank.status_code=200
            cache.set('top_rank',json_top_rank,timeout=86400)
            return(json_top_rank)
        else:
            print('content_cache')
            return top_rank_cache
    finally:
        print('request get /top_rank')
        
@recommend_api.route('/recommend_article', methods=['GET'])##News 標籤推薦API   
def recommend_article():
    hour = datetime.now().hour
    minute = datetime.now().minute
    recommend_article_cache = cache.get('recommend_cache')
    try:
        if (not recommend_article_cache) or \
        ((hour>9 and minute > 0) and (hour>9 and minute <= 2)):
            print('Not cache')
            content = requests.get(f"http://127.0.0.1:8010/recommend_api/content_clear")
            top_rank = requests.get(f"http://127.0.0.1:8010/recommend_api/top_rank")
            content = content.json()       
            top_rank = top_rank.json()
            recommend_article = qr.recommend_article(content,top_rank["top_rank"])
            json_recommend_article = jsonify(recommend_article)
            json_recommend_article.status_code=200
            cache.set('recommend_cache',json_recommend_article,timeout=86400)
            return(json_recommend_article)
        else:
            print('content_cache')
            return recommend_article_cache
    finally:
        print('request get /recommend_article')
        
@recommend_api.route('/user_prefer', methods=['GET'])##News 標籤推薦API   
def user_prefer():
    hour = datetime.now().hour
    minute = datetime.now().minute
    prefer_cache = cache.get('prefer_cache')
    try:
        if (not prefer_cache) or \
        ((hour>9 and minute > 0) and (hour>9 and minute <= 2)):
            df_users_prefer_score = qr.user_prefer()
            js_user_prefer_score = dataframe_to_json(df_users_prefer_score)
            json_user_prefer = jsonify(js_user_prefer_score)
            json_user_prefer.status_code=200
            cache.set('prefer_cache',json_user_prefer,timeout=7200)
            return(json_user_prefer)
        else:
            print('prefer_cache')
            return prefer_cache
    finally:
        print('request get /prefer_cache')        
        
@recommend_api.route('/user_recommend', methods=['GET'])##News 標籤推薦API   
def user_recomment():
    hour = datetime.now().hour
    minute = datetime.now().minute
    user_article_recommend = cache.get('user_article_recommend')
    try:
        if (not user_article_recommend) or \
        ((hour>9 and minute > 0) and (hour>9 and minute <= 2)):
            df_users_prefer_score = requests.get(f"http://127.0.0.1:8010/recommend_api/user_prefer")
            recommend_article = requests.get(f"http://127.0.0.1:8010/recommend_api/recommend_article")
            top_rank = requests.get(f"http://127.0.0.1:8010/recommend_api/top_rank")
            df_users_prefer_score = pd.DataFrame.from_records(df_users_prefer_score.json())
            recommend_article = recommend_article.json()
            top_rank = top_rank.json()
            df_user_recommend = qr.user_recomment(df_users_prefer_score,recommend_article,top_rank["top_rank"])
            df_user_recommend["recommend_article"] = [','.join(map(str, l)) for l in df_user_recommend['recommend_article']]
            js_user_recommend = dataframe_to_json(df_user_recommend)
            json_user_recommend = jsonify(js_user_recommend)
            json_user_recommend.status_code=200
            cache.set('user_article_recommend',json_user_recommend,timeout=86400)
            return(json_user_recommend)
        else:
            print('user_article_recommend')
            return user_article_recommend
    finally:
        print('request get /user_article_recommend')       
    
@recommend_api.route('/pid_search', methods=['POST'])
def request_pid_search():
    post_json  = request.get_json(force=True)
    pid = str(post_json["pid"])
    article_num = int(post_json["article_num"])
#    pid = request.args.get('pid',type = str)
#    quantity = request.args.get("quantity", 10, type = int)
    
    user_recommend = requests.get(f"http://127.0.0.1:8010/recommend_api/user_recommend")
    user_recommend = pd.DataFrame.from_records(user_recommend.json())
    
    if pid in user_recommend.values: 
        faq = user_recommend[user_recommend["pid"]==pid]
        faq = ("".join(faq["recommend_article"].to_list())).split(",")
        if article_num<=10:    
            faq = faq[0:11]
        else:
            faq = faq[0:article_num+1]
        output = {pid:faq}
        return jsonify(output)
    
    else:
        error = {"error":"This pid is not exist."}
        return jsonify(error)

    
##error message       
@recommend_api.app_errorhandler(404)
def not_found(e):
#    news.logger.error(f"not found:{e},route:{request.url}")
    message={
            'status':404,
            'message': 'not found ' + request.url
            }
    resp = jsonify(message)
    resp.status_code = 404
    return resp

@recommend_api.app_errorhandler(500)
def server_error(e):
#    news.logger.error(f"Server error:{e},route:{request.url}")
    message={
            'status':500,
            'message': 'server error ' + request.url
            }
    resp = jsonify(message)
    resp.status_code = 500
    return resp

@recommend_api.app_errorhandler(403)
def forbidden(e):
#    news.logger.error(f"Forbidden access:{e},route:{request.url}")
    message={
            'status':403,
            'message': 'server error ' + request.url
            }
    resp = jsonify(message)
    resp.status_code = 403
    return resp