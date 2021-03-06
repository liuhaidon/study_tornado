#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import tornado.web
import tornado.ioloop
from tornado.options import define, options
from view.admin_test import *

define("ip", default="162.247.101.143", help="run on the given port", type=str)
define("port", default=8066, help="run on the given port", type=int)
define("develop", default=True, help="develop environment", type=bool)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/admin/test/param", AdminParam),     # 参数测试
            (r"/admin/test/result", AdminResult),   # 参数测试

            (r"/login_code", LoginCode),            # 验证码测试
            (r"/image_code", ImageCode),            # 验证码测试

            (r"/(.*)", NotFoundHandler),               # 未定义路由处理
        ]
        settings = dict(
            xsrf_cookies=True,   # https://www.jianshu.com/p/96994db07f03
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,     # debug调试模式，当为True，文件保存后server会自动重启，默认False。
        )
        self.settings = settings
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)

    print("visit at", "http://127.0.0.1:%s" % options.port)
    tornado.ioloop.IOLoop.instance().start()
