#!/usr/bin/env python
# -*- coding:utf-8 -*-
import tornado.web
import os, time, pymongo
import functools
# import urlparse
from tornado.web import HTTPError
from db import database
from utils.session import *
from utils.logger import *
# from db.database import database as mongodb
try:
    from urllib import quote
    from urlparse import urlparse
    from urllib import urlencode
    import urllib2 as request
except ImportError:
    from urllib.parse import quote
    from urllib.parse import urlparse
    from urllib.parse import urlencode
    import urllib.request as request


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.session = Session(self.application.session_manager, self)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Origin", "https://www.bt.cn")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with,content-type")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        # self.set_header("Access-Control-Max-Age", 1000)
        # self.set_header("Content-type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

    # def get_current_user(self):
    #     # return self.session.get("user_name")
    #     return self.get_secure_cookie("user")

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
            print("login failed")
            return False
        self.logging.info(('login checked', userid, password))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        ip = self.request.remote_ip
        user = self.db.tb_user_profile.find_one({'userid': userid}, {'passwd': 0, '_id': 0})
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

        print("sssssss=>", store)
        # self.session['name'] = store.get('loginid')
        self.session['data'] = store
        self.session["loginid"] = userid
        self.session.save()
        return True

    def end_frontend_session(self):
        # id = self.get_secure_cookie("session_id")
        # print "end_frontend_session=",id
        # self.application.sessions.clear_session(id)

        print(self.session)
        if self.session is not None:
            username = self.session['loginid']
            # print uid,username
            self.db.tb_store_profile.update({'loginid': username}, {'$set': {'status': 'offline'}})
            self.application.frontend_auth.logout(username)
        self.session['loginid'] = None
        self.session.save()

    # mysql
    def begin_backend_session(self, sysid, password):
        self.logging.info(('start login', sysid, password))
        logger().info(('start login', sysid, password))
        user = self.application.dbutil.isloginsuccess(sysid, password)   # mysql数据库
        if not user:
            print("login failed")
            return False
        self.logging.info(('login checked', sysid, password))

        # 添加用户登录记录
        name = "登陆用户：" + sysid if type(sysid) != bytes else "登陆用户：" + sysid.decode()
        ip_info = self.request.remote_ip
        logtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        sql = "insert into tb_login_record values(null, '%s', '%s', '%s')" % (name, ip_info, logtime)
        self.application.dbutil.execute(sql)

        # 查找该用户的所有权限
        # permission = self.application.dbutil.getFindPermission(sysid)
        # arr = []
        # for p in permission:
        #     arr.append(p["title"])

        self.session["data"] = user
        self.session["sysid"] = sysid
        # self.session['permission'] = arr
        self.session.save()
        return True

    # mongo
    def begin_backend_session1(self, sysid, password):
        self.logging.info(('start login', sysid, password))
        logger().info(('start login', sysid, password))
        if not self.application.backend_auth.login(sysid, password):       # mongodb数据库
            print("login failed")
            return False
        self.logging.info(('login checked', sysid, password))
        user = self.db.tb_system_user.find_one({'userid': sysid}, {'passwd': 0, '_id': 0})
        if not user:
            print("no user exists!",sysid)
            return False

        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        last = self.db.tb_login_record.find_one({}, {"id": 1, "_id": 0}, sort=[("id", pymongo.DESCENDING)])
        id = int(last.get("id", 0)) + 1 if last else 1
        ip_info = self.request.remote_ip
        self.db.tb_login_record.insert({"userid": sysid, "ip": ip_info, "atime": now, "id": id})

        # user["db"] = self.application.settings["database"]
        # user["system"] = self.application.settings["system"]
        logininfos = user.get('login', [])
        logininfos.append({"ip": ip_info, "time": now})
        self.db.tb_system_user.update({'userid': sysid}, {'$set': {'status': 'online', "login": logininfos[-10:]}})
        user['status'] = "online"
        user['login'] = logininfos[-10:]
        print("==========================",logininfos,logininfos[-10:])
        print(user['login'])

        # 查找该用户的所有权限
        # permission = self.application.dbutil.getFindPermission(sysid)
        # arr = []
        # for p in permission:
        #     arr.append(p["title"])

        self.session["data"] = user
        self.session["sysid"] = sysid
        # self.session['permission'] = arr
        self.session.save()
        return True

    def end_backend_session(self):
        # id = self.get_secure_cookie("session_id")
        # self.application.sessions.clear_session(id)
        if self.session is not None:
            username = self.session['sysid']
            # self.db.tb_system_user.update({'userid': username}, {'$set': {'status': 'offline'}})
            # self.application.backend_auth.logout(username)
            self.clear_cookie("username")
            # self.application.backend_auth.logout(username)
        self.session['sysid'] = None
        self.session.save()

    def get_login_url(self):
        self.require_setting("login_url", "@authenticated")   # @tornado.web.authenticated
        return self.application.settings["login_url"]

    @classmethod
    def authenticated(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # if not self.get_current_user:
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
            if not self.session.get('sysid'):
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_admin_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)
            # else:
                # if self.session['data'].get("role", "") != "superadmin":
                # if self.session['data'].get("role", "admin") != "superadmin":
                        # raise HTTPError(403)
                        # self.redirect('/admin/login')
                        # return
            return method(self, *args, **kwargs)
        return wrapper

    @classmethod
    def wechat_authenticated(cls, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            skey = self.request.headers.get('skey', None)
            if skey:
                tbl_user = mongodb.getDB().get_collection("tb_user_profile")
                tbl_user.find_one({"skey":skey})

            if not self.session.get('skey'):
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

    @classmethod
    def api_authentication(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            print("haah")
        return wrapper
