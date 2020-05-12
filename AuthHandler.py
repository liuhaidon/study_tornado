import functools
import tornado.web
from tornado.escape import utf8
from hashlib import md5


class AuthHandler(tornado.web.RequestHandler):
    realm = "liu_hai_dong"
    basic_auth_conf = "config/basic_auth.json"

    def __init__(self, *argc, **argkw):
        super(AuthHandler, self).__init__(*argc, **argkw)

    @classmethod
    def basic_authenticated(cls, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Authorization: Basic base64("user:passwd")
            auth_header = self.request.headers.get('Authorization', None)
            if auth_header is not None:   # Basic YWRtaW46YWRtaW4=
                auth_mode, auth_base64 = auth_header.split(' ', 1)
                assert auth_mode == 'Basic'
                
                auth_username, auth_password = auth_base64.encode('utf-8').decode('base64').split(':', 1)
                if auth_username == username or auth_password == password:
                    self.write('ok')
                else:
                    self.write('fail')
            else:
                '''
                HTTP/1.1 401 Unauthorized
                WWW-Authenticate: Basic realm="ren_jie"
                '''
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'Basic realm="%s"' % cls.realm)
            return method(self, *args, **kwargs)
        return wrapper

# https://blog.csdn.net/junfeng666/article/details/79310992
# http://xiaorui.cc/archives/1904
# https://blog.csdn.net/yypsober/article/details/50718716
# https://zhidao.baidu.com/question/1450826798120826540.html
