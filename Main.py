#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import tornado.ioloop
import tornado.web
from tornado.options import define, options

from view.ajax import *
from view.front import *
from view.admin_mysql import *
from view.admin_api import *
from db.mysql import DBUtil
from utils.session import *
# from utils.ueditor import *
# from utils.pay import *

# from session.session import MongoSessions
# from session.auth import MongoAuthentication
# reload(sys)
# sys.setdefaultencoding("utf-8")

from routes.api_handler import api_urls
from routes.record_handler import record_urls
# from routes.alipay_handler import alipay_urls
# from routes.dingding_handler import ding_ding_urls

define("domain", default="", help="run on the given domain", type=str)
define("ip", default="162.247.101.143", help="run on the given port", type=str)
define("port", default=8066, help="run on the given port", type=int)
define("develop", default=True, help="develop environment", type=bool)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            # (r"/", index),
            # (r"/index", index),
            (r"/login", user_login),
            (r"/logout", user_logout),

            (r"/admin/home", AdminHomeHandler),
            (r"/admin/login", AdminLoginHandler),
            (r"/admin/logout", AdminLogoutHandler),

            # (r"/admin/users", AdminUserList),
            # (r"/admin/user/add", AdminAddUser),
            # (r"/admin/user/delete", AdminDeleteUser),
            # # (r"/admin/user/audit", AdminAuditUser),
            # # (r"/admin/user/([0-9a-z]{24})", AdminModifyUser),
            #
            (r"/admin/sysusers", AdminSysUsers),
            (r"/admin/sysuser/add", AdminAddSysUser),
            (r"/admin/sysuser/delete", AdminDeleteSysUser),
            (r"/admin/sysuser/([0-9a-z]{24})", AdminModifySysUser),
            (r"/admin/system/repass", AdminRepassSystem),

            # (r"/admin/permissions", AdminPermissions),
            # (r"/admin/permission/add", AdminAddPermission),
            # (r"/admin/permission/delete", AdminDeletePermission),
            #
            # (r"/admin/media/contents", AdminContents),
            #
            # (r"/ajax/sysuser/find", AjaxFindSysUser),
            # (r"/ajax/permission/bind", AjaxBindPermission),  # 点击权限绑定
            # (r"/ajax/bind/permission", AjaxPermissionBind),  # 点击确定
            #
            # (r"/admin/notices", AdminNoticeList),
            # (r"/admin/notice/add", AdminAddNotice),
            # (r"/admin/notice/delete", AdminDeleteNotice),
            # # (r"/admin/notice/([0-9a-z]{24})", AdminModifyNotice),
            #
            # (r"/ajax/upload_image", UploadImageFile),        # 上传图片
            # (r"/ajax/upload_video", UploadVideoFile),        # 上传视频
            # (r"/admin/media/upload", RemotePictureHandler),   # 上传富文本：还要改动html页面与ueditor.py页面
        ]
        handlers.extend(api_urls)         # api路由
        handlers.extend(record_urls)      # 记录路由（登录记录、操作记录）
        # handlers.extend(alipay_urls)      # 支付路由
        # handlers.extend(ding_ding_urls)   # 钉钉路由
        self.dbutil = DBUtil()
        # self.sessions = MongoSessions("tornado", "sessions", timeout=30)
        # self.frontend_auth = MongoAuthentication("tornado", "tb_store_profile", "phone")
        # self.backend_auth = MongoAuthentication("tornado", "tb_system_user", "userid")
        # self.sessions.clear_all_sessions()
        settings = dict(
            cookie_secret="e446976943b4e8442f099fed1f3fea28462d5832f483a0ed9a3d5d3859f==78d",
            xsrf_cookies=True,
            login_url="/login",
            admin_login_url="/admin/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            upload_path=os.path.join(os.path.dirname(__file__), "static/media"),
            json_path=os.path.join(os.path.dirname(__file__), "json"),
            attachment_path=os.path.join(os.path.dirname(__file__), "attachment"),
            debug=True,     # debug调试模式，当为True，文件保存后server会自动重启，默认False。
            develop_env="true",
            session_secret="3cdcb1f00803b6e78ab50b466a40b9977db396840c28307f428b25e2277f1bcc",
            session_timeout=1800,
            store_options={
                'redis_host': '127.0.0.1',
                'redis_port': 6379,
                'redis_pass': 'redis123',        # requirepass
            },
            appid="wxdf26791ff0f192e5",
            appsecret="f159318a4cf52422cf7720dae392bf0e",
            timeout=7200,
            record_of_one_page=10,
            # ui_modules={
            #     "VideosListDisplay": VideosListDisplay,
            #     "ParticipantsListDisplay": ParticipantListDisplay,
            # }
        )
        self.settings = settings
        tornado.web.Application.__init__(self, handlers, **settings)
        self.session_manager = SessionManager(settings["session_secret"], settings["store_options"],
                                              settings["session_timeout"])


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)

    # scheduler_job(app)      # 执行计划任务，定时推送任务
    # load_base_data(app)

    print("visit at", "http://127.0.0.1:%s" % options.port)
    tornado.ioloop.IOLoop.instance().start()

# 源码解析：https://www.cnblogs.com/jasonwang-2016/p/5950548.html
