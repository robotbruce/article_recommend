# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 02:45:27 2021

@author: bruceyu1113
"""
import requests
#import pandas as pd


#content = requests.get(f"http://127.0.0.1:8010/recommend_api/content_clear")
#content = content.json()
#
#top_rank = requests.get(f"http://127.0.0.1:8010/recommend_api/top_rank")
#top_rank = top_rank.json()
#
#recommend_article = requests.get(f"http://127.0.0.1:8010/recommend_api/recommend_article")
#recommend_article = recommend_article.json()
#
#user_prefer = requests.get(f"http://127.0.0.1:8010/recommend_api/user_prefer")
#user_prefer = pd.DataFrame.from_records(user_prefer.json())
#
#user_recommend = requests.get(f"http://127.0.0.1:8010/recommend_api/user_recommend")
#user_recommend = pd.DataFrame.from_records(user_recommend.json())

post_pid = {"pid":"002a058d-40d4-4883-9556-4015a516df88","article_num":15}
output = requests.post(f"http://127.0.0.1:8010/recommend_api/pid_search",json = post_pid)
recommend_output = output.json()

