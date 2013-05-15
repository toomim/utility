#!/usr/bin/env python

# Import libraries
import time
import hmac
import hashlib
import base64
import urllib
import xml.dom.minidom
import csv
from datetime import datetime, timedelta
import traceback
import types
from dal import *
import gluon.contrib.simplejson as json
# import autoreload
# autoreload.run()

# Define constants
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
SERVICE_NAME = 'AWSMechanicalTurkRequester'
#SERVICE_VERSION = '2007-06-21'
SERVICE_VERSION = '2008-04-01'

SANDBOXP = False
LOCAL_EXTERNAL_P = True



# ==================================
#  Calling mturk with REST API
# ==================================

def generate_timestamp(gmtime):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", gmtime)

def generate_signature(service, operation, timestamp, secret_access_key):
    my_sha_hmac = hmac.new(secret_access_key, service + operation + timestamp, hashlib.sha1)
    my_b64_hmac_digest = base64.encodestring(my_sha_hmac.digest()).strip()
    return my_b64_hmac_digest


def ask_turk_raw(operation, args):
    assert AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

    # Calculate the request authentication parameters
    timestamp = generate_timestamp(time.gmtime())
    signature = generate_signature('AWSMechanicalTurkRequester', operation, timestamp, AWS_SECRET_ACCESS_KEY)

    # Construct the request
    parameters = {
        'Service': SERVICE_NAME,
        'Version': SERVICE_VERSION,
        'AWSAccessKeyId': AWS_ACCESS_KEY_ID,
        'Timestamp': timestamp,
        'Signature': signature,
        'Operation': operation
        }

    parameters.update(args)

    # Make the request
    if SANDBOXP:
        url = 'https://mechanicalturk.sandbox.amazonaws.com/onca/xml?'
    else:
        url = 'https://mechanicalturk.amazonaws.com/onca/xml?'
    result_xmlstr = urllib.urlopen(url, urllib.urlencode(parameters)).read()
    return result_xmlstr

def ask_turk(operation, args):
    """
    The main function everything uses.

    Raises a TurkAPIError if shit goes down.
    """
    return xmlify(ask_turk_raw(operation, args))

# ==================================
#  Handling errors
# ==================================

class TurkAPIError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

amazon_health_log = []
def error_rate():
    amazon_health_log = store_get('amazon_health_log')
    if not amazon_health_log: return 0.0
    recent = amazon_health_log[-200:]
    return float(recent.count('error')) / float(len(recent))
def error_check(result_xml):
    # Check for and print results and errors
    errors_nodes = result_xml.getElementsByTagName('Errors')
    if errors_nodes:
        msg = 'There was an error processing your request:'
        for errors_node in errors_nodes:
            for error_node in errors_node.getElementsByTagName('Error'):
                msg += '\n  Error code:    ' + error_node.getElementsByTagName('Code')[0].childNodes[0].data
                msg += '\n  Error message: ' + error_node.getElementsByTagName('Message')[0].childNodes[0].data
        store_append('amazon_health_log', 'error')
        raise TurkAPIError(msg)

    store_append('amazon_health_log', 'ok', max_length=400)
    return False


# ==================================
#  Code for manipulating XML
# ==================================

def xmlify(result):
    try:
        result_xml = xml.dom.minidom.parseString(result.encode('utf-8'))
    except:
        message = "Parsing error on %s\n  Error: %s\n%s" \
            % (result,
               str(sys.exc_info()[1]),
               ''.join(traceback.format_tb(sys.exc_info()[2])))
        raise TurkAPIError(message)
    error_check(result_xml)
    prettyable(result_xml)
    return result_xml

try:
    from os import sys
except:
    pass

def pp(doc):
    print doc.toprettyxml().replace('\t', '   ')
def prettyable(doc):
    doc.pp = types.MethodType(pp, doc)
    return doc

def get(xmlobj, tagname):
    """
    Get something from an xml object.  If you have:
    
     <thing>
       <foo>
         3
       </foo>
     </thing>

    Then you can use get(object, 'foo') to get the 3.
    """
    a = xmlobj.getElementsByTagName(tagname)
    if len(a) > 1:
        print "===//// Shit, lots of " + tagname + "'s!!!"
        print "Shit, lots of " + tagname + "'s!!!"
        print "===\\\\\\\\ Shit, lots of " + tagname + "'s!!!"
    return len(a) > 0 and a[0].firstChild.data

def gets(xmlobj, tagname):
    """
    Like get, but for arrays: finds all foos and returns them all in a
    big array.
    """
    a = xmlobj.getElementsByTagName(tagname)
    return map(lambda x: (x.firstChild.data), a)

def getx(xmlobj, tagname):
    """
    Like get, but returns the XML object of the subtree instead of its
    data.
    """
    return getsx(xmlobj, tagname)[0]
def getsx(xmlobj, tagname):
    """
    Like getx, but for arrays, like gets.
    """
    return xmlobj.getElementsByTagName(tagname)



# ==================================
#  Code for API calls to mturk
# ==================================


def balance():
    return ask_turk('GetAccountBalance',{})

def print_balance():
    pp(ask_turk('GetAccountBalance',{}))

def get_hit(hitid):
    return ask_turk('GetHIT', {'HITId' : hitid})

def hit_creation(hit):
    time = get(hit, 'CreationTime')
    if not time:
        pp(hit)
        raise Exception, 'This hit %s has no creation time' % gets(hit,'HITId')
    tmp = time.split('T')
    tmp[1] = tmp[1][:-1]
    date = map(lambda x: int(x), tmp[0].split('-'))
    time = map(lambda x: int(x), tmp[1].split(':'))
    result = datetime(date[0], date[1], date[2], time[0], time[1], time[2])
    return result

def get_page(operation, page):
    data = ask_turk(operation, {'PageSize' : 100, \
                            'PageNumber' : page,\
                            'SortProperty' : 'Enumeration'})
    print 'Getting page ' + str(page) + ' with '\
          + get(data, 'NumResults') + ' hits of '\
          + get(data,'TotalNumResults')
    return gets(data,'HITId')
    
def get_all_pages(operation):
    results = []
    i = 1
    while True:
        hits = get_page(operation, i)
        if len(hits) == 0:
            break
        results += hits
        i = i+1
    return results
    
def get_hits_to(startdate):
    results = []
    i = 1
    while True:
        hits = get_page(operation, i)
        if len(hits) == 0 or False:
            break
        results += hits
        i = i+1
    return results
    
def get_all_hits ():
    return get_all_pages('SearchHITs')

recent_hits = []
def load_recent_hits():
    next_page = 1 + len(recent_hits)/100
    recent_hits.extend(get_page('SearchHITs', next_page))
    print "You've now loaded %s hits, dating back to %s" \
          % (len(recent_hits),
             str(hit_creation(get_hit(recent_hits[-1]))))

##    data = ask_turk('SearchHITs', {'PageSize' : 100})
##    return gets(data, 'HITId')

def get_reviewable_hit_ids ():
    return get_all_pages('GetReviewableHITs')

def get_assignments_for_hit(hitid):
    data = ask_turk('GetAssignmentsForHIT', {
        'HITId' : hitid})
    return getsx(data, 'Assignment')

def get_worker_answers(hitid):
     assignments = get_assignments_for_hit(hitid)
     result = map(lambda ass:
                  [ass.firstChild.firstChild.data,
                   ass.getElementsByTagName('Answer')[0].firstChild.data],
                  assignments)
     return result
    

def is_valid(xmlobj):
    return get(xmlobj, 'IsValid') and get(xmlobj, 'IsValid') == "True"

def get_hit_status(hitid):
    hit = get_hit(hitid)
    return is_valid(hit) and get(hit,'HITStatus')

def get_my_assignments ():
    return map(get_assignments_for_hit, get_all_hits())
def get_responses():
    hits = get_all_hits()
    for i,hit in enumerate(hits):
        print 'Processing hit ' + str(i) + ': ' + hit
        assignments = get_assignments_for_hit(hit)
        for ass in assignments:
            state = get(ass,'AssignmentStatus')
            if state == 'Rejected':
                print '## skipping REJECTED assignment ' + get(ass,'AssignmentId')
            elif state == 'Submitted' or state == 'Approved':
                answerText = get(ass,'Answer')
                answerXML = xmlify(answerXML)
                guesses = gets(answerXML, 'FreeText')
                
            else:
                print '###################### ERRRRROOOOOORRRRRRRR'


def bonus_total(ass_id):
    bonus_sum = 0.0
    bonuses = get_bonus_payments(ass_id)
    if int(get(bonuses, 'NumResults')) > 0:
        for bonus in gets(bonuses, 'Amount'):
            #print ass_id + ' got a bonus of ' + str(float(bonus))
            bonus_sum += float(bonus)
    return bonus_sum

def give_bonus_up_to(assignmentid, workerid, bonusamt, reason):
    '''
    Returns 0 if the assignment is already bonused that much.
    Throws error if doesn't work.
    Else you can assume the bonus has been given when this is done.
    Returns the amount added to the bonus.
    '''
    existing_bonus = bonus_total(assignmentid)
    if existing_bonus >= bonusamt:
        return False
    new_bonus = bonusamt - existing_bonus
    give_bonus(assignmentid, workerid, new_bonus, reason)
    return new_bonus

def give_bonus(assignmentid, workerid, bonusamt, reason):
    params = {'AssignmentId' : assignmentid,
              'WorkerId' : workerid,
              'BonusAmount.1.Amount' : bonusamt,
              'BonusAmount.1.CurrencyCode' : 'USD',
              'Reason' : reason}
    return ask_turk('GrantBonus', params)

def get_bonus_payments(assignmentid):
    params = {'AssignmentId' : assignmentid,
              'PageSize' : 100}
    return ask_turk('GetBonusPayments', params)



def approve_assignment(assignmentid):
    params = {'AssignmentId' : assignmentid\
              #,'RequesterFeedback' : 'Correct answer was "'+answer+'"'
              }
    return ask_turk('ApproveAssignment', params)
   
def verify_approve_assignment(assid):
    r = approve_assignment(assid)
    return get(r,'IsValid') and not get(r, 'Error') and not get(r, 'Errors')

def assignment_status(assid, hitid):
    asses = get_assignments_for_hit(hitid)
    for ass in asses:
        if assid == get(ass, 'AssignmentId'):
            return get(ass, 'AssignmentStatus')
    return None

def reject_assignment(assignmentid):
    params = {'AssignmentId' : assignmentid\
              #,'RequesterFeedback' : 'Correct answer was "'+answer+'"'
              }
    return ask_turk('RejectAssignment', params)
   
    

def disable_hit(hitid):
    # Turns it off, but it stays on amazon's servers
    params = {'HITId' : hitid}
    print 'Killing hit ' + hitid
    return ask_turk('DisableHIT', params)

def disable_all_hits():
    for hit in get_all_hits():
        disable_hit(hit)

def dispose_hit(hitid):
    # disables and deletes it from amazon's servers
    params = {'HITId' : hitid}
    print 'Killing hit ' + hitid
    return ask_turk('DisposeHIT', params)

def dispose_all_hits():
    return "this is dangerous! you sure? edit the code if you mean it"
    for hit in get_all_hits():
        dispose_hit(hit)

def expire_hit(hitid):
    params = {'HITId' : hitid}
    #print 'Killing hit ' + hitid
    return ask_turk('ForceExpireHIT', params)

def expire_all_hits():
    for hit in get_all_hits():
        expire_hit(hit)

def approve_all_hits():
    for hit in get_reviewable_hit_ids():
        asses = get_assignments_for_hit(hit)
        print "Looking at assignments ", asses.toprettyxml(), ' for ', hit
        for ass in asses:
            ass = get(ass, 'AssignmentId')
            approve_assignment(ass)


import urllib
# duration should be a minute or so.  maybe 4... why not.
def register_hit_type(title, description, reward, duration, keywords):
    params = {'Title' : title,
              'Description' : description,
              'Reward.1.Amount' : reward,
              'Reward.1.CurrencyCode' : 'USD',
              'AssignmentDurationInSeconds' : duration,
              'Keywords' : keywords}
    return ask_turk('RegisterHITType', params)


# no_india_qual = dict(QualificationTypeId = '00000000000000000071',
#                      Comparator='NotEqualTo',
#                      LocaleValue='IN', IntegerValue=None)
def create_hit(question, title, description, keywords, ass_duration, lifetime, assignments=1, reward=0.0, tag=None, block_india=False, block_usa=False):
    params = {'Title' : title,
              'Question' : question,
              'MaxAssignments' : assignments,
              'RequesterAnnotation' : tag,
              'Description' : description,
              'Reward.1.Amount' : reward,
              'Reward.1.CurrencyCode' : 'USD',
              'AssignmentDurationInSeconds' : ass_duration,
              'LifetimeInSeconds' : lifetime,
              'Keywords' : keywords
              }

    if block_india:
        params['QualificationRequirement.1.QualificationTypeId']='00000000000000000071'
        params['QualificationRequirement.1.Comparator']='EqualTo'
        params['QualificationRequirement.1.LocaleValue.Country']='US'
        params['QualificationRequirement.1.RequiredToPreview']=True
    if block_usa:
        params['QualificationRequirement.2.QualificationTypeId']='00000000000000000071'
        params['QualificationRequirement.2.Comparator']='NotEqualTo'
        params['QualificationRequirement.2.LocaleValue.Country']='US'
        params['QualificationRequirement.2.RequiredToPreview']=True

    result = ask_turk('CreateHIT', params)
    update_hit(xml=result)
    return result
    

def external_question(url, frame_height):
    return """<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
  <ExternalURL>""" + url + """</ExternalURL>
  <FrameHeight>""" + str(frame_height) + """</FrameHeight>
</ExternalQuestion>"""

def register_external_hit(url, frame_height, tag=None):
    return register_hit(external_question(url, frame_height), tag)


def external_url(controller_and_func):
    if LOCAL_EXTERNAL_P and SANDBOXP:
        return 'http://localhost:8000/init/' + controller_and_func
    else:
        return 'http://friendbo.com:8111/init/' + controller_and_func

def hit_url(hitxml):
    ''' hitxml can either be a hit response from createhit, or xmlcache '''
    if SANDBOXP:
        url = 'http://workersandbox.mturk.com/mturk/preview?groupId='
    else:
        url = 'http://www.mturk.com/mturk/preview?groupId='
    groupid = hitxml.getElementsByTagName('HITTypeId')[0].firstChild.data
    hitid = get(hitxml, 'HITId')
    return url + groupid + '&hitId=' + hitid


import webbrowser
def openhit(hitxml):
    webbrowser.open_new_tab(hit_url(hitxml))


def message_worker(workerid, subject, body):
    params = {'Subject' : subject,
              'MessageText' : body,
              'WorkerId' : workerid
              }
    return ask_turk('NotifyWorkers', params)
    
def message_workers(workerids, subject, body):
    params = {'Subject' : subject,
              'MessageText' : body
              }

    for i,wid in enumerate(workerids):
        params['WorkerId.'+str(i)] = wid

    return ask_turk('NotifyWorkers', params)
    
def block_worker(workerid, reason):
    params = {'WorkerId' : workerid,
              'Reason' : reason
              }
    return ask_turk('BlockWorker', params)

def add_turk_fees(hit_price):
    return max(.005, hit_price + hit_price*.1)


# ==================================
#  Logging hits to database
# ==================================
#now=datetime.now()

database = 'hits.db' if SANDBOXP else 'hits-sandbox.db'
db = DAL('sqlite://' + database)

db.define_table('hits',
                db.Field('hitid', 'text'),
                db.Field('status', 'text', default='open'),
                db.Field('xmlcache', 'text'), # Local copy of mturk xml
                db.Field('launch_date', 'datetime'),
                db.Field('other', 'text')) # Not used yet...

db.define_table('assignments',
                db.Field('assid', 'text'),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('ip', 'text'),
                db.Field('status', 'text'),
                db.Field('xmlcache', 'text'),
                # How did I use this flag?  Don't recall.
                #db.Field('cache_dirty', 'boolean', default=True),
                db.Field('accept_time', 'datetime'),
                # Need to update 'paid' to include the amount paid in
                # NON-BONUS rewards. My code only paid in bonus.
                db.Field('paid', 'double', default=0.0),
                db.Field('other', 'text', default=''))

db.define_table('store',
                db.Field('key', 'text', unique=True),
                db.Field('value', 'text'))

def update_hit(xml=None, hitid=None):
    if xml:
        hitid = get(xml, 'HITId')

    assert(hitid)
    xml = get_hit(hitid)

    row = db.hits(hitid = hitid)
    if not row:
        row = db.hits.insert(hitid = hitid,
                             launch_date = datetime.now())
    row.update_record(xmlcache = xml.toxml(),
                      status = get(xml, 'HITStatus'))
    db.commit()

def update_hits():
    hits = db.hits.all()
    for i,hit in enumerate(hits):
        print ('Updating hit %s/%s' % (i+1, len(hits)))
        update_hit(hitid=hit.hitid)

def print_hits(n=None):
    rows = db(db.hits.id > 0).select(db.hits.id,
                                     db.hits.hitid,
                                     db.hits.launch_date,
                                     db.hits.status)
    if n:
        rows = rows[max(0,len(rows)-n):]
    print rows
def print_asses(n=None, minutes_ago=None):
    query = (db.assignments.id > 0)
    if minutes_ago:
        query = query & (db.assignments.accept_time > (datetime.now() - timedelta(minutes=minutes_ago)))
    rows = db(query).select(db.assignments.id,
                            db.assignments.paid,
                            db.assignments.hitid,
                            db.assignments.assid,
                            db.assignments.workerid,
                            db.assignments.status)
    if n:
        rows = rows[max(0,len(rows)-n):]
    print rows

def update_asses(n=None):
    hits = db.hits.all()
    if n:
        hits = hits[max(0,len(hits)-n):]
    for i,hit in enumerate(hits):
        print ('Updating asses for hit %s/%s' % (i+1, len(hits)))
        asses = get_assignments_for_hit(hit.hitid)
        for ass in asses:
            assid = get(ass, 'AssignmentId')
            bonus_amount = bonus_total(assid)

            row = db.assignments(assid = assid)
            params = dict(assid=assid,
                          hitid=hit.hitid,
                          workerid=get(ass, 'WorkerId'),
                          status=get(ass, 'AssignmentStatus'),
                          paid = bonus_amount, # Oversimplification
                          xmlcache = ass.toxml())
            if row:
                row.update_record(**params)
            else:
                db.assignments.insert(**params)
            db.commit()

def fetch_from_amazon(n=None):
    hits = db.hits.all()
    if n:
        hits = hits[max(0,len(hits)-n):]
    for i,hit in enumerate(hits):
        print ('Updating asses and hit %s/%s' % (i+1, len(hits)))
        update_hit(hitid=hit.hitid)
        asses = get_assignments_for_hit(hit.hitid)
        for ass in asses:
            assid = get(ass, 'AssignmentId')
            bonus_amount = bonus_total(assid)

            row = db.assignments(assid = assid)
            params = dict(assid=assid,
                          hitid=hit.hitid,
                          workerid=get(ass, 'WorkerId'),
                          status=get(ass, 'AssignmentStatus'),
                          paid = bonus_amount, # Oversimplification
                          xmlcache = ass.toxml())
            if row:
                row.update_record(**params)
            else:
                db.assignments.insert(**params)
            db.commit()
    

# ==================================
#  Boilerplate database helper functions I use in every DAL
# ==================================

# These are some helpers I like in every web2py DAL project
import types
for table in db.tables:
    def first(self):
        return db(self.id>0).select(orderby=self.id, limitby=(0,1)).first()
    def last(self, n=1):
        rows = db(self.id>0).select(orderby=~self.id, limitby=(0,n))
        if n==1: return rows.first()
        return rows
    def all(self, *stuff, **rest):
        return db(self.id>0).select(*stuff, **rest)
    t = db[table]
    t.first = types.MethodType(first, t)
    t.last = types.MethodType(last, t)
    t.all = types.MethodType(all, t)

def lazy(f):
   def g(self,f=f):
       import copy
       self=copy.copy(self)
       return lambda *a,**b: f(self,*a,**b)
   return g

def extra_db_methods_vf(clss):
   ''' This decorator clears virtualfields on the table and replaces
       them with the methods on this class.
   '''
   # First let's make the methods lazy
   for k in clss.__dict__.keys():
      if type(getattr(clss, k)).__name__ == 'instancemethod':
         setattr(clss, k, lazy(getattr(clss, k)))

   tablename = clss.__name__.lower()
   if not tablename in db:
      raise Error('There is no `%s\' table to put virtual methods in' % tablename)
   del db[tablename].virtualfields[:] # We clear virtualfields each time
   db[tablename].virtualfields.append(clss())
   return clss

def store_get(key):
    r = db(db.store.key==key).select().first()
    return r and json.loads(r.value)
def store_set(key, value):
    value = json.dumps(value); record = db.store(db.store.key==key)
    result = record.update_record(value=value) \
        if record else db.store.insert(key=key, value=value)
    db.commit()
    return result
def store_append(key, value, max_length=None):
    x = store_get(key) or []; x.append(value)
    if max_length and len(x) > max_length:
        x = x[-max_length:]
    return store_set(key, x)

# ==================================
#  DB helper methods
# ==================================

class Hits():
    def open(self):
        openhit(xmlify(self.hits.xmlcache))
Hits = extra_db_methods_vf(Hits)

class Assignments():
    def get_status(self):
        return assignment_status(self.assignments.assid,
                                 self.assignments.hitid)
    def approve(self):
        if self.assignments.status == u'Rejected':
            print 'Rejected this guy'
            return 'Rejected'
        if self.assignments.status == u'Approved':
            return 'Done'
        try:
            result = approve_assignment(self.assignments.assid)
            return result
        except TurkAPIError, e:
            status = self.assignments.get_status()
            if status == u'Approved':
                self.assignments.update_record(status=status)
                db.commit()
                return 'Already done'
            else:
                print e
                print 'Status is %s' % self.assignments.get_status()
                return 'Error... bla'
    def reject(self):
        if self.assignments.status == u'Rejected':
            return 'Done'
        if self.assignments.status == u'Approved':
            print 'Approved this guy'
            return 'Approved'
        try:
            result = reject_assignment(self.assignments.assid)
            return result
        except TurkAPIError, e:
            status = self.assignments.get_status()
            if status == u'Rejected':
                self.assignments.update_record(status=status)
                db.commit()
                return 'Already done'
            else:
                print e
                print 'Status is %s' % self.assignments.get_status()
                return 'Error... bla'
        
    def bonus_up_to(self, amount, reason):
        if self.assignments.paid < amount:
            val = give_bonus_up_to(self.assignments.assid,
                                   self.assignments.workerid,
                                   amount, reason)
            self.assignments.update_record(paid = amount)
            db.commit()
            return val
        else:
            return 'Already paid this ass $%s' % amount

    def amount_paid(self):
        result = 0.0
        # Get approval amount
        if self.assignments.status == u'Approved':
            hit = db.hits(hitid=self.assignments.hitid)
            result += add_turk_fees(float(get(xmlify(hit.xmlcache), 'Amount')))
        # Add in bonus amount
        if self.assignments.paid > 0.0:
            result += add_turk_fees(self.assignments.paid)

        return result

Assignments = extra_db_methods_vf(Assignments)

db.assignments.total_paid = \
    types.MethodType(lambda table: sum([x.amount_paid() for x in table.all()]),
                     db.assignments)
