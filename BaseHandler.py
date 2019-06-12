#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import logging
import tornado.web
import time
import functools
import urlparse
import datetime

from tornado.web import HTTPError
from db import database
from utils.session import *
from urllib import urlencode
from view.logger import *
def datediff(beginDate, endDate):
    """计算时间相差天数，输入格式为：str"""
    format = "%Y-%m-%d %H:%M:%S"
    bd = datetime.datetime.strptime(beginDate, format)
    ed = datetime.datetime.strptime(endDate, format)
    oneday = datetime.timedelta(days=1)
    count = 0
    while bd.date() < ed.date():
        ed = ed - oneday
        count += 1
    return count


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.session = Session(self.application.session_manager, self)

    def get_current_user(self):
        return self.session.get("user_name")

    @property
    def get_session(self):
        return self.session

    @property
    def db(self):
        return database.database.getDB()

    def auth(self):
        if not self.session:
            self.redirect('/login')

    @property
    def logging(self):
        logging.basicConfig(level=logging.WARN,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(os.path.dirname(__file__), "log") + "web.log",
                            filemode='w')
        return logging

    @property
    def user(self):
        if self.session.get("loginid"):
            return self.session['data']
        else:
            return None

    @property
    def admin(self):
        if self.session.get("sysid"):
            return self.session['data']
        else:
            return None

    @property
    def permission(self):
        if self.session.get("permission"):
            return self.session['permission']
        else:
            return None

    def begin_frontend_session(self, userid, password):
        self.logging.info(('start login', userid, password))
        if not self.application.frontend_auth.login(userid, password):
            print "login failed"
            return False
        self.logging.info(('login checked', userid, password))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        ip = self.request.remote_ip
        # user = self.db.tb_user_profile.find_one({'userid': userid}, {'passwd': 0, '_id': 0})
        # # print user
        # logininfos = user.get('login', [])
        # print "login==>",logininfos
        # logininfos.append({"ip": ip, "time": now})
        # m=self.db.tb_user_profile.update({'userid': userid}, {'$set': {'status': 'online', "login":logininfos[-10:]}})
        # # print m

        store = self.db.tb_store_profile.find_one({"loginid": userid}, {'passwd': 0, '_id': 0})
        logininfos = store.get('login', [])
        m = self.db.tb_store_profile.update({'loginid': userid},
                                            {'$set': {'status': 'online', "login": logininfos[-10:]}})
        store['status'] = "online"
        store['login'] = logininfos[-10:]

        print "sssssss=>", store
        # self.session['name'] = store.get('loginid')
        self.session['data'] = store
        self.session["loginid"] = userid
        self.session.save()
        return True

    def end_frontend_session(self):
        # id = self.get_secure_cookie("session_id")
        # print "end_frontend_session=",id
        # self.application.sessions.clear_session(id)

        print self.session
        if self.session is not None:
            username = self.session['loginid']
            # print uid,username
            self.db.tb_store_profile.update({'loginid': username}, {'$set': {'status': 'offline'}})
            self.application.frontend_auth.logout(username)
        self.session['loginid'] = None
        self.session.save()

    def begin_backend_session(self, sysid, password):
        logger().info(('start login', sysid, password))
        result = self.application.dbutil.isloginsuccess(sysid, password)
        if not result:
            print "login failed"
            return False
        self.logging.info(('login checked', sysid, password))

        # now = time.strftime('%Y-%m-%d %H:%M:%S')
        # ip = self.request.remote_ip
        # logininfos.append({"ip": ip, "time": now})

        # 查找该用户的所有权限
        permission = self.application.dbutil.getFindPermission(sysid)
        arr = []
        for p in permission:
            arr.append(p["title"])

        self.session['data'] = result
        self.session["sysid"] = sysid
        self.session['permission'] = arr
        self.session.save()
        return True

    def end_backend_session(self):
        # id = self.get_secure_cookie("session_id")
        # self.application.sessions.clear_session(id)
        if self.session is not None:
            username = self.session['sysid']
            self.clear_cookie("username")
            # self.application.backend_auth.logout(username)
        self.session['sysid'] = None
        self.session.save()

    @classmethod
    def authenticated(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            print "session值1===>",self.session
            if not self.session.get('loginid'):
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)

            return method(self, *args, **kwargs)

        return wrapper

    def get_admin_login_url(self):
        self.require_setting("admin_login_url", "@admin_authed")
        return self.application.settings["admin_login_url"]

    @classmethod
    def admin_authed(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            print "session值===>", self.session
            if not self.session.get('sysid'):
                print "没有sysid了"
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_admin_login_url()
                    print "url1===>", url
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        print "next_url===>", next_url
                        url += "?" + urlencode(dict(next=next_url))
                    print "url2===>", url
                    self.redirect(url)
                    return
                raise HTTPError(403)
            return method(self, *args, **kwargs)
        return wrapper