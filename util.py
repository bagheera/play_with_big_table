from google.appengine.ext import db

def purge(entity_name):
      q = db.GqlQuery("SELECT * FROM "+entity_name)
      results = q.fetch(1000)
      db.delete(results)

