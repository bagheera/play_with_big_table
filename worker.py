import os
import logging
import string
import random
import util

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

def randstr(length):
    return "".join(random.sample(string.letters, length))

class Worker(db.Model):
    id = db.StringProperty()
    num_daughters = db.IntegerProperty(default=0)
    num_sons = db.IntegerProperty(default=0)
    
    @staticmethod
    def generate():
        return Worker(id=randstr(8))
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self,other):
        return not(self.__eq__(other))

class Child(db.Model):
    name = db.StringProperty()
    gender = db.StringProperty()
    age = db.IntegerProperty()
    guardian = db.ReferenceProperty(Worker, collection_name="children")
    guardianKey = db.StringProperty()
    
    def male(self):
        return self.gender == 'M'
    
    def teen(self):
        return self.age > 12 and self.age < 19
    
    @staticmethod
    def generate(worker):
        mf = ['M','F']
        for count in xrange(1, random.randint(2,8)):
           c = Child(name=randstr(5), 
                                   gender = mf[random.randint(31,91) % 2], 
                                   age = random.randint(1,30), guardian=worker, guardianKey = str(worker.key()))
           if c.teen():
               if c.male():
                   logging.info("num_sons:"+str(c.guardian.id) + str(c.guardian.num_sons))
                   c.guardian.num_sons += 1
               else:
                   logging.info("num_daughters:"+str(c.guardian.id) + str(c.guardian.num_daughters))
                   c.guardian.num_daughters += 1               
           c.put()
           c.guardian.put()
                                   
    
class LoadWorkers(webapp.RequestHandler):
    def add_failsafe_result(self):   
        emp = Worker(id="dummy")
        emp.put()
        c1 = Child(name="d1", gender='F', age=15, guardian=emp, guardianKey = str(emp.key()))
        c2 = Child(name="d2", gender='F', age=17, guardian=emp, guardianKey = str(emp.key()))
        c1.guardian.num_daughters += 1               
        c1.put()
        c1.guardian.put()
        c2.guardian.num_daughters += 1               
        c2.put()
        c2.guardian.put()
        
    def get(self):
        util.purge('Worker')
        util.purge('Child')    
        self.add_failsafe_result()
        for count in xrange(1,20):
            emp = Worker.generate()
            emp.put()
            Child.generate(emp)
        
        
class FindTeenagers(webapp.RequestHandler):
    def get(self):
        emps = db.GqlQuery("SELECT * FROM Worker WHERE num_daughters = 2")
        workers = []
        for w in emps.fetch(1000):
            logging.info("found worker:" + w.id)
            workers.append(str(w.key()))
        teens = db.GqlQuery("SELECT * FROM Child WHERE gender='F' and age > 12 and age < 19 and guardianKey IN :1", workers)
        result = []
        for teen in teens.fetch(1000):
            logging.info("found teen"+ teen.name)
            result.append(teen)
        template_values = { 'teens': result}
        path = os.path.join(os.path.dirname(__file__), 'teens.html')
        self.response.out.write(template.render(path, template_values))
        