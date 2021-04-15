# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 02:01:14 2021

@author: bruceyu1113
"""

from flask import Flask
from cache import cache

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["JSON_AS_ASCII"] = False
    app.config['CACHE_TYPE']='simple'
    
    cache.init_app(app)
    
    from article_recommend.routes import recommend_api
    app.register_blueprint(recommend_api)
    return(app)


if __name__ == '__main__':
    # from flask_cache import Cache
    app = create_app()
    app.run(host="0.0.0.0",port=8010,debug=True, use_reloader=False)

