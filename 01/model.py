from google.appengine.ext import ndb
from google.appengine.ext import blobstore


# A model for a user
class User(ndb.Model):
    account = ndb.StringProperty()
    password = ndb.StringProperty()
    name = ndb.StringProperty()
    birthDate = ndb.StringProperty()

class Message(ndb.Model):
    account = ndb.StringProperty()
    text = ndb.StringProperty()
    created = ndb.DateTimeProperty()

class Company(ndb.Model):
    name = ndb.StringProperty()
    url = ndb.StringProperty()
    image = ndb.BlobProperty()
    uploaded = ndb.BooleanProperty()

class ServiceTerms(ndb.Model):
    file = ndb.BlobProperty()
    
class Privacy(ndb.Model):
    file = ndb.BlobProperty() 
    
class VideoIndex(ndb.Model):
    index=ndb.StringProperty()
    title=ndb.StringProperty()
    
class UserVideo(ndb.Model):
    user = ndb.StringProperty()
    blob_key = blobstore.BlobReferenceProperty()
  

      
