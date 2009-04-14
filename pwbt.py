import cgi
import wsgiref.handlers
import os
import logging
import worker
import util

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from datetime import date
from datetime import datetime

class Region(db.Model):
    id = db.IntegerProperty()
    name = db.StringProperty()
    
class Country(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()
    region = db.ReferenceProperty(Region, collection_name="countries")

class Location(db.Model):
    id = db.IntegerProperty()
    address = db.PostalAddressProperty()
    country = db.ReferenceProperty(Country)

class Job(db.Model):
    id = db.StringProperty()
    title = db.StringProperty()
    min_salary = db.IntegerProperty()
    max_salary = db.IntegerProperty()

class Employee(db.Model):
    pass

class Department(db.Model):
    id = db.IntegerProperty()
    name = db.StringProperty()
    manager = db.ReferenceProperty(Employee, collection_name="managed_departments")
    location = db.ReferenceProperty(Location, collection_name="departments")

class Employee(db.Model):
    id = db.IntegerProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    email = db.EmailProperty()
    phone_number = db.PhoneNumberProperty()
    hire_date = db.DateProperty()
    job = db.ReferenceProperty(Job)
    salary = db.FloatProperty()
    commission_pct = db.FloatProperty()
    manager = db.SelfReferenceProperty(collection_name="reportees")
    department = db.ReferenceProperty(Department, collection_name="employees")
    
    def prev_job(self):
        find_prev = db.GqlQuery('SELECT * FROM JobHistory WHERE employee = :1 ORDER BY start_date DESC', self)
        result = find_prev.fetch(1)
        if len(result) == 0:
            return None
        return result[0]
 
class JobHistory(db.Model):
    employee = db.ReferenceProperty(Employee, collection_name="job_history")
    start_date = db.DateProperty()
    end_date = db.DateProperty()
    job = db.ReferenceProperty(Job)
    department = db.ReferenceProperty(Department)
    
class DocFamilyMember(db.Property): 
    def __init__(self, name, relation, age):
        self.name = name
        self.relation = relation
        self.age = age
    
    def __not__(self):
        return not(name)

    def __eq__(self, other):
        return self.name == other.name and self.relation == other.relation and self.age== other.age
    
    def __ne__(self, other):
        return not self.__eq__(other)

class DocFamilyMemberProperty(db.Property): 
    data_type = DocFamilyMember
        
    def get_value_for_datastore(self, model_instance):
        member = super(DocFamilyMemberProperty, #what does this do?
                 self).get_value_for_datastore(model_instance)
        return member.name + ',' + member.relation + ',' + member.age
    
    def make_value_from_datastore(self, value):
        if value is None:
            return None;
        fields = value.split(',');
        return DocFamilyMember(fields[0], fields[1], fields[2])
    
    
class DocEmployee(db.Model):
    name = db.StringProperty()
    spouse = DocFamilyMemberProperty()
    #    children = db.ListProperty(item_type=DocFamilyMember)#seems can only be smthing like a primitive type
    
class PlayWithBigTable(webapp.RequestHandler):
  def get(self, *args):
      self.purge("JobHistory")
      self.purge("Employee")
      self.purge("Department")
      self.purge("Job")
      self.purge("Location")
      self.purge("Country")
      self.purge("Region")
      self.purge("DocEmployee")
      r = Region(id=1111, name="asia-pacific")
      r.put()
      c = Country(id="IN", name="india", region=r)
      c.put()
      addr = db.PostalAddress("1600 Ampitheater Pkwy., Mountain View, CA")
      loc = Location(id=2222, country=c, address = addr)
      loc.put()
      j = Job(id="M101", name="MingleMonkey", min_salary=100000, max_salary=150000)
      j.put()
      j2 = Job(id="E123", name="CodeMonkey", min_salary=10000, max_salary=80000)
      j2.put()
      j3 = Job(id="E125", name="Architect", min_salary=70000, max_salary=150000)
      j3.put()
      dep = Department(id=231, name="IS", location=loc)
      dep.put()
      mgr = Employee(id=345678, first_name="Chaman",last_name="Lal",email=db.Email("chaman.lal@bigtable.com"),
                     phone_number=db.PhoneNumber("1 (206) 555-1212"), hire_date=date(date.today().year, 1, 20), job=j, salary=125000.5,commission_pct=7.2,department=dep)
      mgr.put()
      emp = Employee(id=456789, first_name="Magan",last_name="Lal",email=db.Email("magan.lal@bigtable.com"),
                     phone_number=db.PhoneNumber("1 (206) 555-1232"), hire_date=date(date.today().year-2, 4, 1), job=j3, salary=60000.0, manager=mgr,department=dep)
      emp.put()
      jh= JobHistory(employee=emp, start_date=date(date.today().year-2,4,5), end_date=date(date.today().year-1,11,11),job=j2,department=dep)
      jh.put()
      sp = DocFamilyMember(name="gx", relation="wife", age="29")
      demp = DocEmployee(name="kris", spouse=sp)
      demp.children.add(DocFamilyMember(name="lx", relation="daughter", age="3"))
      demp.children.add(DocFamilyMember(name="yy", relation="son", age="7"))
      demp.put()
  
class Detail():
    def __init__(self, **args):
        self.region_id  = args.get("region_id")
        self.region_name  = args.get("region_name")
        self.country_id  = args.get("country_id")
        self.country_name  = args.get("country_name")
        self.loc_id  = args.get("loc_id")
        self.loc_address  = args.get("loc_address")
        self.job_id  = args.get("job_id")
        self.job_title  = args.get("job_title")
        self.min_salary  = args.get("min_salary")
        self.max_salary  = args.get("max_salary")
        self.dept_id  = args.get("dept_id")
        self.dept_name  = args.get("dept_name")

        self.emp_id  = args.get("emp_id")
        self.emp_first_name  = args.get("emp_first_name")
        self.emp_last_name  = args.get("emp_last_name")
        self.emp_email  = args.get("emp_email")
        self.emp_phone_number  = args.get("emp_phone_number")
        self.emp_hire_date  = args.get("emp_hire_date")
        self.emp_job  = args.get("emp_job")
        self.emp_salary  = args.get("emp_salary")
        self.emp_commission_pct  = args.get("emp_commission_pct")
        self.emp_department  = args.get("emp_department")

        self.mgr_id  = args.get("mgr_id")
        self.mgr_first_name  = args.get("mgr_first_name")
        self.mgr_last_name  = args.get("mgr_last_name")
        self.mgr_email  = args.get("mgr_email")
        self.mgr_phone_number  = args.get("mgr_phone_number")
        self.mgr_commission_pct  = args.get("mgr_commission_pct")
        
        self.prev_job_start_date  = args.get("prev_job_start_date")
        self.prev_job_end_date  = args.get("prev_job_end_date")
        self.prev_job_id  = args.get("prev_job_id")
        self.prev_job_title  = args.get("prev_job_title")
        self.prev_job_dept  = args.get("prev_job_dept")

    def get_row(self):
        row = "<tr>"
        for attr in dir(self):
            row += "<td>"
            row += str(self.__dict__.get(attr, ""))
            row += "</td>"
        row += "</tr>"
        return row
    
    @staticmethod    
    def get_header():
        dummy = Detail()
        row = "<tr>"
        for attr in dir(dummy):
            row += "<th>"
            row += attr
            row += "</th>"
        row += "</tr>"
        return row
        
class Report(webapp.RequestHandler):
    def get_detail(self,emp):
        d = Detail(
            region_id  = emp.department.location.country.region.id,
            region_name = emp.department.location.country.region.name,  
            country_id  = emp.department.location.country.id,
            country_name  = emp.department.location.country.name,
            loc_id  = emp.department.location.id,
            loc_address  = emp.department.location.address,
            job_id  = emp.job.id,
            job_title  = emp.job.title,
            min_salary  = emp.job.min_salary,
            max_salary  = emp.job.max_salary,
            dept_id  = emp.department.id,
            dept_name  = emp.department.name,
            emp_id = emp.id,  
            emp_first_name  = emp.first_name,
            emp_last_name  = emp.last_name,
            emp_email  = emp.email,
            emp_phone_number  = emp.phone_number,
            emp_hire_date  = emp.hire_date,
            emp_salary = emp.salary  
               )
        if emp.manager:
            d.mgr_id = emp.manager.id
            d.mgr_first_name  = emp.manager.first_name
            d.mgr_last_name  = emp.manager.last_name
            d.mgr_email  = emp.manager.email
            d.mgr_phone_number  = emp.manager.phone_number
            d.mgr_commission_pct  = emp.manager.commission_pct
        p = emp.prev_job()
        if p:
            d.prev_job_start_date = p.start_date,  
            d.prev_job_end_date  = p.end_date,
            d.prev_job_id  = p.job.id,
            d.prev_job_title  = p.job.title,
            d.prev_job_dept = p.department.name                 

        return d


    def get(self, since):
        find_emps = db.GqlQuery("SELECT * FROM Employee WHERE hire_date >DATE('"+since+"')")#datetime.strptime(since, "%Y-%m-%d").date())
        emps = find_emps.fetch(1000)
        details = map(self.get_detail, emps)
        template_values = { 'items': details, 'header': Detail.get_header() }
        path = os.path.join(os.path.dirname(__file__), 'report.html')
        self.response.out.write(template.render(path, template_values))

def main():
  application = webapp.WSGIApplication(
                                       [('/pwbt/load_data', PlayWithBigTable),
                                        (r'/pwbt/load_workers', worker.LoadWorkers),
                                        (r'/pwbt/teenagers', worker.FindTeenagers),
                                        (r'/pwbt/report/(.*)', Report)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()