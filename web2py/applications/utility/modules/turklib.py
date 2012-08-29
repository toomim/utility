#!/usr/bin/env python

# Import libraries
import time
import hmac
import hashlib
import base64
import urllib
import xml.dom.minidom
import csv
import datetime
import traceback
# import autoreload
# autoreload.run()

# Define constants
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
SERVICE_NAME = 'AWSMechanicalTurkRequester'
#SERVICE_VERSION = '2007-06-21'
SERVICE_VERSION = '2008-04-01'

SANDBOXP = True                         # Loaded from help.py
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

def error_check(result_xml):
    # Check for and print results and errors
    errors_nodes = result_xml.getElementsByTagName('Errors')
    if errors_nodes:
        msg = 'There was an error processing your request:'
        for errors_node in errors_nodes:
            for error_node in errors_node.getElementsByTagName('Error'):
                msg += '\n  Error code:    ' + error_node.getElementsByTagName('Code')[0].childNodes[0].data
                msg += '\n  Error message: ' + error_node.getElementsByTagName('Message')[0].childNodes[0].data
        raise TurkAPIError(msg)

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
    return result_xml

try:
    from os import sys
except:
    pass

def pp(doc):
    print doc.toprettyxml().replace('\t', '   ')


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
    Like get, but for arrays.  If there's lots of foos, return them
    all in a big array.
    """
    a = xmlobj.getElementsByTagName(tagname)
    return map(lambda x: (x.firstChild.data), a)

def getx(xmlobj, tagname):
    """
    Like get, but returns the XML object instead of its data.
    """
    return getsx(xmlobj, tagname)[0]
def getsx(xmlobj, tagname):
    """
    Like getx, but for arrays, like gets.
    """
    return xmlobj.getElementsByTagName(tagname)



############## code from up_hits ################

import webbrowser
#from xml.sax import saxutils
#import codecs

def balance():
    return ask_turk('GetAccountBalance',{})

def print_balance():
    pp(ask_turk('GetAccountBalance',{}))

def getHit(hitid):
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
    result = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2])
    return result

def getPage(operation, page):
    data = ask_turk(operation, {'PageSize' : 100, \
                            'PageNumber' : page,\
                            'SortProperty' : 'Enumeration'})
    print 'Getting page ' + str(page) + ' with '\
          + get(data, 'NumResults') + ' hits of '\
          + get(data,'TotalNumResults')
    return gets(data,'HITId')
    
def getAllPages(operation):
    results = []
    i = 1
    while True:
        hits = getPage(operation, i)
        if len(hits) == 0:
            break
        results += hits
        i = i+1
    return results
    
def getHitsTo(startdate):
    results = []
    i = 1
    while True:
        hits = getPage(operation, i)
        if len(hits) == 0 or False:
            break
        results += hits
        i = i+1
    return results
    
def getAllHits ():
    return getAllPages('SearchHITs')

recent_hits = []
def load_recent_hits(num_pages):
    next_page = 1 + len(recent_hits)/100
    recent_hits.extend(getPage('SearchHITs', next_page))
    print "You've now loaded %s hits, dating back to %s" \
          % (len(recent_hits),
             str(hit_creation(getHit(recent_hits[-1]))))

##    data = ask_turk('SearchHITs', {'PageSize' : 100})
##    return gets(data, 'HITId')

def getReviewableHitIDs ():
    return getAllPages('GetReviewableHITs')

def getAssignmentsForHit(hitid):
    data = ask_turk('GetAssignmentsForHIT', {
        'HITId' : hitid})
    return getsx(data, 'Assignment')

def getWorkerAnswers(hitid):
     assignments = getAssignmentsForHit(hitid)
     result = map(lambda ass:
                  [ass.firstChild.firstChild.data,
                   ass.getElementsByTagName('Answer')[0].firstChild.data],
                  assignments)
     return result
    

def isValid(xmlobj):
    return get(xmlobj, 'IsValid') and get(xmlobj, 'IsValid') == "True"

def getHitStatus(hitid):
    hit = getHit(hitid)
    return isValid(hit) and get(hit,'HITStatus')

def getMyAssignments ():
    return map(getAssignmentsForHit, getAllHits())
def getResponses():
    hits = getAllHits()
    for i,hit in enumerate(hits):
        print 'Processing hit ' + str(i) + ': ' + hit
        assignments = getAssignmentsForHit(hit)
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
    bonuses = getBonusPayments(ass_id)
    if int(get(bonuses, 'NumResults')) > 0:
        for bonus in gets(bonuses, 'Amount'):
            #print ass_id + ' got a bonus of ' + str(float(bonus))
            bonus_sum += float(bonus)
    return bonus_sum

def giveBonusUpTo(assignmentid, workerid, bonusamt, reason):
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
    giveBonus(assignmentid, workerid, new_bonus, reason)
    return new_bonus

def giveBonus(assignmentid, workerid, bonusamt, reason):
    params = {'AssignmentId' : assignmentid,
              'WorkerId' : workerid,
              'BonusAmount.1.Amount' : bonusamt,
              'BonusAmount.1.CurrencyCode' : 'USD',
              'Reason' : reason}
    return ask_turk('GrantBonus', params)

def getBonusPayments(assignmentid):
    params = {'AssignmentId' : assignmentid,
              'PageSize' : 100}
    return ask_turk('GetBonusPayments', params)



def approveAssignment(assignmentid):
    params = {'AssignmentId' : assignmentid\
              #,'RequesterFeedback' : 'Correct answer was "'+answer+'"'
              }
    return ask_turk('ApproveAssignment', params)
   
def verifyApproveAssignment(assid):
    r = approveAssignment(assid)
    return get(r,'IsValid') and not get(r, 'Error') and not get(r, 'Errors')

def assignmentStatus(assid, hitid):
    asses = getAssignmentsForHit(hitid)
    for ass in asses:
        if assid == get(ass, 'AssignmentId'):
            return get(ass, 'AssignmentStatus')
    return None

def rejectAssignment(assignmentid):
    params = {'AssignmentId' : assignmentid\
              #,'RequesterFeedback' : 'Correct answer was "'+answer+'"'
              }
    return ask_turk('RejectAssignment', params)
   
    

def disableHit(hitid):
    # Turns it off, but it stays on amazon's servers
    params = {'HITId' : hitid}
    print 'Killing hit ' + hitid
    return ask_turk('DisableHIT', params)

def disable_all_hits():
    for hit in getAllHits():
        disableHit(hit)

def disposeHit(hitid):
    # disables and deletes it from amazon's servers
    params = {'HITId' : hitid}
    print 'Killing hit ' + hitid
    return ask_turk('DisposeHIT', params)

def dispose_all_hits():
    return "this is dangerous! you sure? edit the code if you mean it"
    for hit in getAllHits():
        disposeHit(hit)

def expireHit(hitid):
    params = {'HITId' : hitid}
    #print 'Killing hit ' + hitid
    return ask_turk('ForceExpireHIT', params)

def expire_all_hits():
    for hit in getAllHits():
        expireHit(hit)

def approve_all_hits():
    for hit in getReviewableHitIDs():
        asses = getAssignmentsForHit(hit)
        print "Looking at assignments ", asses.toprettyxml(), ' for ', hit
        for ass in asses:
            ass = get(ass, 'AssignmentId')
            approveAssignment(ass)


import urllib
# duration should be a minute or so.  maybe 4... why not.
def registerHitType(title, description, reward, duration, keywords):
    params = {'Title' : title,
              'Description' : description,
              'Reward.1.Amount' : reward,
              'Reward.1.CurrencyCode' : 'USD',
              'AssignmentDurationInSeconds' : duration,
              'Keywords' : keywords}
    return ask_turk('RegisterHITType', params)


def myhittypeid():
    return u'0XYZHBDVTZ7G7ZSSXKD0' if SANDBOXP else u'XW3ZPWYY5ZXZ5CMP3AKZ'
def registerMyHitType():
    return registerHitType('Guess answers to stranger\'s personal questions ($.25-$.75 bonus for correct answer)',
                           'Guess secret answers to a stranger\'s personal questions. Guess correct in 3 tries and get $.75 bonus.',
                           .05,
                           60*4,
                           'guess, personal questions, bonus')


def captcha_ht():
    return u'4J04MTYMW9DWN91PZY30' if SANDBOXP else u'RXJMSCDYTZBZSAYRFYFZ'
def registerCaptchaHitType():
    return registerHitType('Mystery Task (BONUS)',
                           'Preview to see the hit and how much it pays.  The pay changes for different hits.  You will be paid entirely in the bonus, within minutes of finishing the HIT.',
                           0.00,
                           60*10,
                           'mystery, bonus')

myhittypeid = captcha_ht

def lifetime():
    return 60*60*1 if SANDBOXP else 60*60*3 # 1 hour or 3 hours

assignments = 1

def registerHit(question, tag):
    params = {'Question' : question,
              'HITTypeId' : myhittypeid(),
              'LifetimeInSeconds' : lifetime(),
              'MaxAssignments' : assignments,
              'RequesterAnnotation' : tag
              }
    return ask_turk('CreateHIT', params)

def createHit(question, title, description, keywords, ass_duration, lifetime, assignments=1, reward=0.0, tag=None):
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
    return ask_turk('CreateHIT', params)
    

def externalQuestion(url, frame_height):
    return """<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
  <ExternalURL>""" + url + """</ExternalURL>
  <FrameHeight>""" + str(frame_height) + """</FrameHeight>
</ExternalQuestion>"""

def registerExternalHit(url, frame_height, tag=None):
    return registerHit(externalQuestion(url, frame_height), tag)


def external_url(controller_and_func):
    if LOCAL_EXTERNAL_P and SANDBOXP:
        return 'http://localhost:8000/utility/' + controller_and_func
    else:
        return 'http://friendbo.com:8111/utility/' + controller_and_func

def hit_url(hitresponse):
    if SANDBOXP:
        url = 'https://workersandbox.mturk.com/mturk/preview?groupId='
    else:
        url = 'https://www.mturk.com/mturk/preview?groupId='
    groupid = hitresponse.getElementsByTagName('HITTypeId')[0].firstChild.data
    hitid = get(hitresponse, 'HITId')
    return url + groupid + '&hitId=' + hitid


def openhit(hitresponse):
    webbrowser.open_new_tab(hit_url(hitresponse))



def messageWorker(workerid, subject, body):
    params = {'Subject' : subject,
              'MessageText' : body,
              'WorkerId' : workerid
              }
    return ask_turk('NotifyWorkers', params)
    
def messageWorkers(workerids, subject, body):
    params = {'Subject' : subject,
              'MessageText' : body
              }

    for i,wid in enumerate(workerids):
        params['WorkerId.'+str(i)] = wid

    return ask_turk('NotifyWorkers', params)
    
