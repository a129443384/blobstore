# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7


import webapp2
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import users
from google.appengine.ext.blobstore import BlobInfo
import os
import cgi
from gaesessions import get_current_session
from model import *
import hashlib
import datetime
from google.appengine.api import mail
import random
import urllib
import urllib2


class Apply(webapp2.RequestHandler):
    def get(self):
        render(self, 'apply.html')

    def post(self):
        name = self.request.get('name')
        account = self.request.get('account')
        password = self.request.get('password')
        if name=='' or account=='' or password=='':
            render(self, 'apply.html', {'error': '請填寫所有欄位'})
            return
            # Check whether the user already exists 
        if User.get_by_id(account):
            render(self, 'apply.html', {'error': '帳號已存在'})
            return
        # Create the User object
        user = User(id=account)
        user.name = name
        user.account = account
        password = password.encode('utf-8')
        user.password = hashlib.sha1(password).hexdigest() # Encrypt the password
        user.birthDate = self.request.get('birthDate')
        user.put()
        # Log the user in
        session = get_current_session()
        if session.is_active():
            session.terminate()
        # start a session for the user (old one was terminated)
        session['account'] = account
        render(self, 'main.html', {'account':account})

class ViewVideo(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, video_key):
        if not blobstore.get(video_key):
            self.error(404)
        else:
            self.send_blob(video_key)
            
class Videoplay(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        videos = VideoIndex.query().fetch()
        render(self, 'videoplay.html', {'videos': videos})
        
        
class UploadVideoForm(webapp2.RequestHandler):
        def get(self):
            upload_url = blobstore.create_upload_url('/uploadVideo')
            # The method must be "POST" and enctype must be set to "multipart/form-data".
            self.response.out.write('<html><body>')
            self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
            self.response.out.write('<p>標題:<input type="text" name="title" /></p>')
            self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
            name="submit" value="Submit"> </form></body></html>''')
        
class UploadVideo(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        title = self.request.get('title')
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        videoIndex = VideoIndex(id=title)
        videoIndex.index = str(blob_info.key())
        videoIndex.title = title
        videoIndex.put()
        render(self, 'main.html')
        
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)        


class Sites(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        render(self, 'sites.html')


class Topics(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        render(self, 'topics.html')


class Main(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        # Initialize data
        companies = Company.query().fetch()
        if not companies:
            for i in range(5):
                company = Company(id='company'+str(i))
                company.put()
        serviceTerms = ServiceTerms.get_by_id('serviceTerms')
        if not serviceTerms:
            serviceTerms = ServiceTerms(id='serviceTerms')
            serviceTerms.put()
        privacy = Privacy.get_by_id('privacy')
        if not privacy:
            privacy = Privacy(id='privacy')
            privacy.put()          
        render(self, 'main.html', {'account':account,
                                   'companies':companies,
                                   'serviceTerms':serviceTerms,
                                   'privacy':privacy})      


class Login(webapp2.RequestHandler):
    def get(self):
        render(self, 'login.html')

    def post(self):
        account = self.request.get('account')
        password = self.request.get('password')
        templateValues = {}
        if account=='' or password=='':
            templateValues.update({'error': '請輸入帳號與密碼'})
            render(self, 'login.html', templateValues)
            return
        user = User.get_by_id(account)
        if not user:
            templateValues.update({'error':'帳號或密碼錯誤'})
            render(self, 'login.html', templateValues)
            return
        password = password.encode('utf-8')
        password = hashlib.sha1(password).hexdigest()
        if password != user.password:
            templateValues.update({'error':'帳號或密碼錯誤'})
            render(self, 'login.html', templateValues)
            return
        # User login successfully
        session = get_current_session()
        if session.is_active():
            session.terminate()
        # start a session for the user (old one was terminated)
        session['account'] = account
        self.response.out.write('success')


class Chat(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        render(self, 'chat.html')
    
    def post(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        templateValues = {}
        if not account:
            templateValues.update({'error': '請先登入'})
            render(self, 'chat.html', templateValues)
            return
        text = self.request.get('text')
        if text == '':
            templateValues.update({'error': '訊息不能空白'})
            render(self, 'chat.html', templateValues)
            return
        message = Message()
        message.account = account
        message.text = text
        message.created = datetime.datetime.now() + datetime.timedelta(hours=8)
        message.put()
        #render(self, 'chat.html', templateValues)
        self.get()


class Members(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        members = User.query().fetch()
        render(self, 'members.html', {'members': members})


class Logout(webapp2.RequestHandler):
    def get(self):
        session = get_current_session()
        if session.is_active():
            session.terminate()
        self.response.out.write('logout')


def checkSession():
    session = get_current_session()
    if session.is_active():
        return session['account']
    return False


class Messages(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account:
            render(self, 'main.html')
            return
        messages = Message.query().order(-Message.created).fetch()
        render(self, 'messages.html', {'messages': messages})


class UploadFiles(webapp2.RequestHandler):
    def get(self):
        account = checkSession()
        if not account or account!='admin':
            render(self, 'main.html')
            return
        companies = Company.query().fetch()
        render(self, 'uploadFiles.html', {'companies':companies})
    
    def post(self):
        account = checkSession()
        if not account or account!='admin':
            render(self, 'main.html')
            return
        arg1 = self.request.get('arg1')
        if arg1 == 'image':
            company = Company.get_by_id(self.request.get('companyId'))
            company.name = self.request.get('name')
            company.url = self.request.get('url')
            company.image = self.request.get('image')
            company.uploaded = True
            company.put()
        else:
            arg2 = self.request.get('arg2')
            if arg2 == 'serviceTerms':
                serviceTerms = ServiceTerms.get_by_id('serviceTerms')
                serviceTerms.file = self.request.get('file')
                serviceTerms.put()
            else:
                privacy = Privacy.get_by_id('privacy')
                privacy.file = self.request.get('file')
                privacy.put()
            #endif
        #endif
        self.get()


class GetImage(webapp2.RequestHandler):
    def get(self):
        entity_id = self.request.get('entity_id')
        if not entity_id:
            return
        entity = ndb.Key(urlsafe=entity_id).get()
        if entity and entity.image:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(entity.image)     

class GetFile(webapp2.RequestHandler):
    def get(self):
        entity_id = self.request.get('entity_id')
        if not entity_id:
            return
        entity = ndb.Key(urlsafe=entity_id).get()
        if entity and entity.file:
            self.response.headers['Content-Type'] = 'text/html'
            self.response.out.write(entity.file)


class SendEmail(webapp2.RequestHandler):
    def get(self):
        sender = 'ABC 網路有限公司 <sino0914@gmail.com>'
        receiver = 'sino0914@gmail.com'
        subject = '電子信箱驗證'
        randNum = random.randint(1000, 9999)
        body = '''
        您好,歡迎加入會員,您的電子信箱驗證碼為:{0}
        
        ABC 網路有限公司  敬上'''.format(randNum)
        body = body.decode('utf-8')
        mail.send_mail(sender, receiver, subject, body)
        #render(self, 'mainMessage.html', {'mainMessage': '已寄出電子郵件'})
        self.response.out.write('<p style="text-align:center;">已寄出電子郵件</p>')


class SendSMS(webapp2.RequestHandler):
    def get(self):
        username = 'aaaaa'
        password = 'a'
        mobile = '0000000000'
        random.seed()
        message = '您的通關密碼為: ' + str(random.randint(1000, 9999))
        message = urllib.quote(message)
        msg = ('&username=' + username + '&password=' + password + '&mobile=' + mobile +
        '&message=' + message)
        url = 'http://api.twsms.com/smsSend.php?' + msg
        resp = urllib2.urlopen(url)
        self.response.out.write('<p style="text-align:center;">已寄出簡訊</p>')


def render(handler, renderFile, templateValues={}):
    path = os.path.join(os.path.dirname(__file__), 'templates/', renderFile)
    handler.response.out.write(template.render(path, templateValues))


app = webapp2.WSGIApplication([
    ('/videoplay', Videoplay),
    ('/serve/([^/]+)?', ServeHandler),
    ('/viewVideo/([^/]+)?', ViewVideo),
    ('/uploadVideoForm', UploadVideoForm),
    ('/uploadVideo', UploadVideo),
    ('/sites', Sites),
    ('/topics', Topics),
    ('/login', Login),
    ('/logout', Logout),
    ('/apply', Apply),
    ('/members', Members),
    ('/chat', Chat),
    ('/messages', Messages),
    ('/uploadFiles', UploadFiles),
    ('/image', GetImage),
    ('/file', GetFile),
    ('/sendEmail', SendEmail),
    ('/sendSMS', SendSMS),
    ('/.*', Main)],
    debug=True)

