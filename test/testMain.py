# -*- coding:utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import os.path

from tornado.options import define, options
define("port", default=8012, help="run on the given port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        print "获取当前用户"
        return self.get_secure_cookie("username")

class LoginHandler(BaseHandler):
    def get(self):
        print self.request.arguments
        self.render('login.html')

    def post(self):
        print self.request.arguments
        self.set_secure_cookie("username", self.get_argument("username"))
        self.set_cookie("name", self.get_argument("username"))
        self.redirect("/")

class WelcomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        # user1 = self.current_user
        # user2 = self.get_current_user
        user1 = self.get_secure_cookie("name")
        user2 = self.get_cookie("username")
        user3 = self.get_secure_cookie("username")
        user4 = self.get_cookie("name")
        print "user1===>", user1
        print "user2===>", user2
        print "user3===>", user3
        print "user4===>", user4
        self.render('index.html', user=self.current_user)

class LogoutHandler(BaseHandler):
    def get(self):
        if not self.get_argument("logout", None):
            self.clear_cookie("username")
            self.redirect("/")


if __name__ == "__main__":
    tornado.options.parse_command_line()

    settings = {
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
        "xsrf_cookies": True,
        "login_url": "/login"
    }

    application = tornado.web.Application([
        (r'/', WelcomeHandler),
        (r'/login', LoginHandler),
        (r'/logout', LogoutHandler)
    ], **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print("visit at", "http://127.0.0.1:%s" % options.port)
    tornado.ioloop.IOLoop.instance().start()

