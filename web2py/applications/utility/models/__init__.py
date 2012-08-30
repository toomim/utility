import time
start_time = time.time()
'''

I'm abusing this __init__.py file to set up the basic utiliscope
environment.

It:
  1. Loads settings
  2. Sets up the database
  3. Defines the API for hits
  4. Defines a few other helper functions
  5. Loads the current hit and sets up experimental variables
     (Or sets up a testing environment if we're in a /test url)

'''
# Create default settings
defaults = '''
sqlitep = True
sandboxp = True
sandbox_serves_from_localhost_p = False
migratep = True
fake_migratep = False
email_address = 'your@address.com'  # errors will be emailed to you here
database_login_pass = ('login', 'pass')
database_name = 'utility'
server_url = 'localhost'
server_port = 8000
aws_access_key_id = 'fillthisin'
aws_secret_access_key = 'andthistoo'
'''
exec(defaults)

# Load the custom settings file.  Make a default file if it doesn't exist yet.
# XXX: this will fail when we compile apps
import os
settings_file = 'applications/utility/models/settings.py'
if not os.path.exists(settings_file):
    f = file(settings_file, 'a'); f.write(defaults); f.close()
execfile(settings_file)

# A hack used in the ./serve script
if 'LoadSettingsOnly' in globals():
    raise LoadSettingsOnly()

# Import
import applications.utility.modules.turk as turk
from applications.utility.modules.turk import TurkAPIError
import gluon.contrib.simplejson as sj 
from gluon.storage import Storage
import gluon.utils
from datetime import datetime, timedelta

# setup turk library
turk.SANDBOXP = sandboxp
turk.LOCAL_EXTERNAL_P = sandbox_serves_from_localhost_p
turk.AWS_ACCESS_KEY_ID = aws_access_key_id
turk.AWS_SECRET_ACCESS_KEY = aws_secret_access_key

# constants
iframe_height = 650
ass_duration = 60*15            # 15 minutes
hit_lifetime = 60*60*24         # 24 hours

# Set up logging
import logging
logger = logging.getLogger("web2py.app.utility")
logger.setLevel(logging.DEBUG)
log = logger.debug
debug = log

logger_t = logging.getLogger("web2py.app.utilitytasks")
logger_t.setLevel(logging.DEBUG)
debug_t = logger_t.debug

if 'inside_scheduler' in globals():
    debug('We are in the scheduler!')

def is_singleton(v):
    return not isinstance(v,list) or len(v) == 1
def singleton(v):
    return v[0] if isinstance(v,list) else v

# Set the database
if sqlitep:
    database = ('sqlite://%s_sandbox.db' % database_name ) if sandboxp else \
               ('sqlite://%s.db' % database_name)
    db = SQLDB(database)
else:
    database = 'postgres://%s:%s@localhost:5432/%s' % (database_login_pass
                                                       + (database_name,))
    if sandboxp: database += '_sandbox'
    db = SQLDB(database, pool_size=100)
session.connect(request, response, db)  # store sessions in database

# Define the database tables
now=datetime.now()
db.define_table('conditions',
                db.Field('json', 'text'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('studies',
                db.Field('launch_date', 'datetime'),
                db.Field('name', 'text'),
                db.Field('description', 'text'),
                db.Field('controller_func', 'text'),
                db.Field('conditions', 'text'),
                db.Field('results', 'text'),
                db.Field('publish', 'boolean', default=False),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('actions',
                db.Field('study', db.studies),
                db.Field('action', 'text'),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('assid', 'text'),
                db.Field('time', 'datetime', default=now),
                db.Field('ip', 'text'),
                db.Field('condition', db.conditions),
                db.Field('other', 'text'),
                #db.Field('cookieid', 'text'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('dead_zones',
                db.Field('study', db.studies),
                db.Field('start_time', 'datetime'),
                db.Field('end_time', 'datetime'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('runs',
                db.Field('workerid', 'text'),
                db.Field('length', 'integer'),
                db.Field('start_time', 'datetime'),
                db.Field('end_time', 'datetime'),
                db.Field('study', db.studies),
                db.Field('condition', db.conditions),
                db.Field('censored', 'boolean', default=False),
                db.Field('bad', 'boolean', default=False),
                db.Field('other', 'text'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('countdown',
                db.Field('assid', 'text'),
                db.Field('count', 'integer'),
                db.Field('waiting', 'boolean', default=False),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('hits',
                db.Field('hitid', 'text', unique=True),
                db.Field('study', db.studies),

                # Status can be {unlaunched, open, getting done, closed}
                db.Field('status', 'text', default='open'),

                # xmlcache is a local copy of mturk xml
                db.Field('xmlcache', 'text'),

                db.Field('launch_date', 'datetime'),
                db.Field('controller_func', 'text'),

                # Variables passed to the controller
                # -- NO LONGER USED
                db.Field('price', 'double'),
                db.Field('othervars', 'text'),

                # Info for later
                db.Field('url', 'text'),

                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('bonus_queue',
                db.Field('assid', 'text'),
                db.Field('hitid', 'text'),
                db.Field('worker', 'text'),
                db.Field('amount', 'text'),
                db.Field('reason', 'text'),
                db.Field('study', db.studies),
                migrate=migratep, fake_migrate=fake_migratep)
                

db.define_table('assignments',
                db.Field('assid', 'text', unique=True),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('status', 'text'),
                db.Field('xmlcache', 'text'),
                db.Field('cache_dirty', 'boolean', default=True),
                db.Field('accept_time', 'datetime'),
                db.Field('paid', 'double', default=0.0),
                db.Field('condition', db.conditions),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('continents',
                db.Field('code','string'),
                db.Field('name','string'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('countries',
                db.Field('code','string'),
                db.Field('name','string'),
                db.Field('continent', db.continents),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('ips',
                db.Field('from_ip','string'),
                db.Field('to_ip','string'),
                db.Field('country', db.countries),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('workers',
                db.Field('workerid', 'text', unique=True),
                db.Field('cookieid', 'text', default=None),
                db.Field('first_seen', 'datetime', default=now),
                db.Field('last_seen', 'datetime'),
                db.Field('latest_ip', 'text'),
                db.Field('bonus_paid', 'double', default=0.0),
                db.Field('bonus_earned', 'double', default=0.0),
                db.Field('country', db.countries),
                db.Field('time_zone', 'integer'), # hours offset from mine
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('feedback',
                db.Field('time', 'datetime', default=now),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('assid', 'text'),
                db.Field('message', 'text'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('store',
                db.Field('key', 'text', unique=True),
                db.Field('value', 'text'))

# Load the options variable from each hit file... this will fail (like
# settings) if compiled
options = Storage()
# #execfile('applications/utility/models/studies.py')
# if os.path.isfile('applications/utility/models/%s.py' % request.controller):
#     execfile('applications/utility/models/%s.py' % request.controller)
options.fail = { 'price' : 0 }

# Define the API that hit controllers can use
def hit_finished(bonus_amount=None, do_redirect=True):
    log('Hit finished!')
    if request.live:
        status = db.hits(hitid = request.vars.hitId).status
        soft_assert(status == 'getting done' or status == 'open',
                    'Finishing a hit %s that was marked %s instead of getting done!' %
                    (request.vars.hitId, status))
        soft_assert(bonus_amount or is_price(request.price),
                    'Finishing hit %s with no bonus amount %s or price %s' % 
                    (request.vars.hitId, bonus_amount, request.price))

        soft_assert(request.assid and request.workerid and request.hitid,
                    'empty octopus %s %s %s' %
                    (request.assid, request.workerid, request.hitid))


        if request.price:
            record_hit_data(request.hitid, price=request.price)

        # Now let's record this finish, but first check to make sure
        # we haven't done so already
        existing_finishes = \
            db((db.actions.study == request.study)
               & (db.actions.workerid == request.workerid)
               & (db.actions.hitid == request.hitid)
               & (db.actions.assid == request.assid)
               & (db.actions.action == 'finished')).count()
        if existing_finishes == 0:
            record_action('finished')
            if not bonus_amount: bonus_amount = request.price

            if not request.testing:
                enqueue_bonus(request.assid,
                              request.workerid, 
                              request.hitid,
                              bonus_amount,
                              request.study)

                update_ass(assid=request.vars.assignmentId,
                           hitid=request.vars.hitId,
                           workerid=request.vars.workerId,
                           status='finished to us')

                if False:
                    worker = db.workers(workerid = request.vars.workerId)
                    worker.update_record(bonus_earned=worker.bonus_earned + bonus_amount)
        
    if do_redirect: redirect(turk_submit_url())

def record_action(action, other=None):
    hit = request.hitid
    if not hit or request.testing:
        return False

    worker = request.workerid
    ass = request.assid
    ip = request.env.remote_addr
    condition = get_condition(request.condition)
    if other: other = sj.dumps(other, sort_keys=True)

    db.actions.insert(study=request.study,
                      action=action,
                      hitid=hit,
                      workerid=worker,
                      assid=ass,
                      ip=ip,
                      condition=condition,
                      other=other)
save_checkpoint = record_action
save_action = record_action
log_action = record_action

def is_preview():
    ''' Can be preview only if this is live or testing.  Then it's
    preview if we're missing the assignmentId.'''
    return (request.vars.live != None or request.vars.testing != None) \
        and (not request.vars.assignmentId
             or request.vars.assignmentId == 'ASSIGNMENT_ID_NOT_AVAILABLE')

def turk_submit_url():
    #log('Making submit url for live=%s', request.live)
    if request.live:
        return 'https://%s.mturk.com/mturk/externalSubmit?assignmentId=%s&hitId=%s&exitid=ok' \
            % ('workersandbox' if sandboxp else 'www',
               request.assid,
               request.hitid)
    else:
        return URL(c='utiliscope', f='fake_submit_to_turk')


from gluon.scheduler import Scheduler
Scheduler(db
#           dict(send_email=send_email_task,
#                    process_launch_queue_task=process_launch_queue_task,
#                    refresh_hit_status=refresh_hit_status,
#                    process_bonus_queue=process_bonus_queue
#                    )
          )

import random
we_are = random.randint(0,10)
def check_daemon2(task_name, period=None):
    if sqlitep: return False
    period = period or 4

    tasks_query = ((db.scheduler_task.function_name == task_name)
                   & db.scheduler_task.status.belongs(('QUEUED',
                                                       'ASSIGNED',
                                                       'RUNNING',
                                                       'ACTIVE')))

    # Launch a launch_queue task if there isn't one already
    tasks = db(tasks_query).select()
    if len(tasks) > 1:          #  Check for error
        raise Exception('Too many open %s tasks!!!  Noooo, there are %s'
                        % (task_name, len(tasks)))
    if len(tasks) < 1:
        #debug('Len(%s) is %s', task_name, len(tasks))

        if not db.executesql('select pg_try_advisory_lock(1);')[0][0]:
            debug('Tasks table is already locked. We are %s.', we_are)
            return

        # Check again now that we're locked
        if db(tasks_query).count() >= 1:
            debug('Caught a race condition! Glad we got outa there! %s',
                  we_are)
            db.executesql('select pg_advisory_unlock(1);')
            return

        debug('Adding a %s task! as %s', task_name, we_are)
        t = db.scheduler_task.insert(function_name=task_name,
                                     application_name='utility/utiliscope',
                                     task_name=task_name,
                                     stop_time = now + timedelta(days=90000),
                                     repeats=0, period=period,
                                     uuid=task_name)
        db.commit()
        db.executesql('select pg_advisory_unlock(1);')
        #debug('Now len(%s) is %s cause we added %s',
        #      task_name, db(tasks_query).count(), t.id)

    elif tasks[0].period != period:
        debug('Updating period for task %s', task_name)
        tasks[0].update_record(period=period)
        db.commit()

def check_daemon(task_name):
    if sqlitep: return False
    period = 4
    task = db.scheduler_task(uuid=task_name)
    #print ('task is %s' % (not (not task)))
    if not task or task.status not in ('QUEUED', 'ASSIGNED', 'RUNNING', 'ACTIVE') \
            or task.period != period:
        try:
            debug('Inserting or updating %s task.', task_name)
            db.scheduler_task.update_or_insert(db.scheduler_task.uuid==task_name,
                                               status='QUEUED',
                                               function_name=task_name,
                                               application_name='utility/utiliscope',
                                               task_name=task_name,
                                               repeats=0,
                                               period=period,
                                               timeout=None,
                                               uuid=task_name)
            db.commit()
        except Exception:
            # Means we tried to insert a second task due to race condition
            debug('Race condition when inserting scheduler task')
            db.rollback()

check_daemon('process_launch_queue_task')
check_daemon('refresh_hit_status')
check_daemon('process_bonus_queue')
#check_daemon('process_tickets', 30)
db.tasks = db.scheduler_task


# Utility methods
def record_hit_data(hitid,
                    study=None,
                    status=None,
                    xmlcache=None,
                    launch_date=None,
                    controller_func=None,
                    price=None,
                    othervars=None,
                    url=None):

    soft_assert(not xmlcache or (type(xmlcache) == type('sdflkj')
                                 or type(xmlcache) == type(u'sdflkj')),
                'bad xmlcache... it is a ' + str(type(xmlcache)))

    # XXX Consider auto-updating the hit status from xmlcache

    hit = db.hits(hitid=hitid)
    if hit:
        # Not sure how to do this in one call cause I don't
        # understand how optional keyword arguments set to None
        # work when given to update_record().
        if study: hit.update_record(study=study)
        if status: hit.update_record(status=status)
        if xmlcache: hit.update_record(xmlcache=xmlcache)
        if launch_date: hit.update_record(launch_date=launch_date)
        if controller_func: hit.update_record(controller_func=controller_func)
        if price: hit.update_record(price=price)
        if othervars: hit.update_record(othervars=othervars)
        if url: hit.update_record(url=url)
    else:
        logger.error('FAIL!!!! Recording hit %s for the first time' % hitid)
        db.hits.insert(hitid=hitid,
                       study=study,
                       status=status,
                       xmlcache=xmlcache,
                       launch_date=launch_date,
                       controller_func=controller_func,
                       price=price,
                       othervars=othervars,
                       url=url)
        db.commit()
        raise Exception('This is not good... hope you meant it...')
    db.commit()
def update_ass(assid, hitid=None, workerid=None, status=None, paid=None, accept_time=None, xmlcache=None, condition=None):
    '''If xmlcache is provided, automatically fills in the other
    parmeaters, except paid.'''

    dirty = True

    if xmlcache:                 
        # Update our cached fields when we get new real mturk data
        x = turk.xmlify(xmlcache)
        assid = turk.get(x, 'AssignmentId')
        hitid = turk.get(x, 'HITId')
        workerid = turk.get(x, 'WorkerId')
        status = turk.get(x, 'AssignmentStatus')
        accept_time = turk.get(x, 'AcceptTime')
        dirty = False

    ass = db.assignments(assid=assid)
    if not ass:
        db.assignments.insert(assid=assid,
                              hitid=hitid,
                              workerid=workerid,
                              status=status,
                              paid=paid,
                              xmlcache=xmlcache,
                              cache_dirty=dirty,
                              condition=condition)
    else:
        # Not sure how to do this in one call cause I don't understand
        # how optional keyword arguments set to None work when given
        # to update_record().
        if hitid: ass.update_record(hitid=hitid)
        if workerid: ass.update_record(workerid=workerid)
        if status: ass.update_record(status=status)
        if paid: ass.update_record(paid=paid)
        if accept_time: ass.update_record(accept_time=accept_time)
        if xmlcache: ass.update_record(xmlcache=xmlcache)
        if condition: ass.update_record(condition=condition)

        ass.update_record(cache_dirty=dirty)
    db.commit()
def is_price(price): return type(price) == type(0.03)

def send_me_mail(message):
    vars = {'to': email_address,
            'subject': 'mturk email',
            'message': message}
    debug('Scheduling an email task.')
    db.scheduler_task.insert(function_name='send_email',
                             application_name='utility/utiliscope',
                             vars=sj.dumps(vars))

last_time = start_time
def checkpoint(what, do_total_time=False):
    global last_time
    new_time = time.time()
    delta = new_time - (last_time if not do_total_time else start_time)
    message = '%s %.0fms' % (what, delta*1000.0)
    if not do_total_time: last_time = new_time
    debug(message)
    return message

def soft_assert(pred, error_message=None):
    if not pred:
        send_me_mail('ASSERT FAIL ' + error_message)
        log('ASSERT FAIL: ' + str(error_message))
        logger.error('ASSERT FAIL: ' + str(error_message))
def enqueue_bonus(assid, workerid, hitid, maxamount, study=None):
    log('Adding %s to bonus queue for ass %s'
                  % (maxamount, assid))
    db.bonus_queue.insert(
        assid = assid,
        worker = workerid,
        hitid = hitid,
        amount = maxamount,
        reason = 'Completed hit',
        study = study)

response.generic_patterns = ['html']

def make_request_vars_convenient():
    # Make request vars more convenient
    request.hitid = request.vars.hitId
    request.workerid = request.vars.workerId
    request.assid = request.vars.assignmentId
    request.testing = request.vars.testing != None
    request.live = request.vars.live != None
    request.preview = is_preview()
    request.price_string = '$%.2f' % request.price if request.price else None
    request.sandbox = sandboxp

    # Put singleton options for this task (e.g. mystery_task) directly
    # into the options variable
    if request.task and request.task in options and isinstance(options[request.task],dict):
        for k,v in options[request.task].items():
            if is_singleton(v):
                options[k] = singleton(v)



import hashlib
def hash_to_bucket(string, buckets):
    return buckets[ord(hashlib.md5(string[:7]).digest()[0]) % len(buckets)]

def sample_from_conditions(conditions, string):
    '''
    Conditions is of the form {thing1 : [option1,option2], thing2 : [...]...}


    conditions = {
        'price' : [.01, .02],
        'style' : ['pretty', 'ugly'],
        'captchas_per_task' : [10]
        }

    '''
    result = {}
    for i,(k,v) in enumerate(conditions.items()):
        # Make sure each iteration gets different hash by prepending
        # with str(i).  By attaching to front, it won't get cut off in
        # the substring operation [:7] in hash_to_bucket
        s = str(i) + string   
                              
        if is_singleton(v):
            result[k] = singleton(v)
        elif isinstance(v, list):
            result[k] = hash_to_bucket(s, v)
        else:
            soft_assert(False, 'Bad condition')
    return result

def sample_firsts_from_conditions(conditions):
    result = {}
    for (k,v) in conditions.items():
        result[k] = singleton(v) if is_singleton(v) else v[0]
    return result
def get_condition(dict):
    soft_assert(type(dict).__name__ != 'str')
    json = sj.dumps(dict, sort_keys=True)
    c = db.conditions(json=json)
    if not c: c = db.conditions.insert(json=json)
    return c
def task_for(controller, function):
    possible_tasks = ['%s/%s' % (controller, function),
                      controller]
    for t in possible_tasks:
        if t in options and isinstance(options[t], dict):
            return t
    logging.debug('You need to put a task in the options dictionary to match %s/%s',
                  controller, function)
    return '%s/%s' % (controller,function)

def die_and_explode():
    request_str = ''
    for k,v in request.items(): request_str += str(k) + ' ' + str(v) + '\n'
    message = 'Got a bad live hit with\n workerid %s\n hitid %s\n assid %s\n testing %s\n hitlen %s' \
              % (request.vars.workerId,
                 request.vars.hitId,
                 request.vars.assignmentId,
                 request.vars.testing,
                 str(len(db(db.hits.hitid == request.vars.hitId).select())))
    message = message + '\n\n' + request_str
    logger.error(message)
    send_me_mail(message)

    # If there's a hit on amazon that we don't know about, oh no!
    # Big bug in our shit!  We better delete this motherfucker so
    # that nobody else tries to do it.
    if request.vars.hitId \
       and not len(db(db.hits.hitid == request.vars.hitId).select()) > 0:
        try:
            log('########### BAD HIT #############')
            turk.expire_hit(request.vars.hitId)
            log('Expired this hit. ' + request.vars.hitId)
        except:
            log('###### GRRRRR we could not expire this hit %s!  Fix!!' % request.vars.hitId)
    redirect(URL(r=request, f='error'))

def hits_done(workerid, study):
    return db((db.actions.workerid == workerid)
          & (db.actions.study == study)
          & (db.actions.action == 'finished')).count()

def alter_conditions(**new_conditions):
    '''
    Don't use this!  It's scary.  I don't know what happens when
    we change the condition_id for an assignment.  Will we be able to
    track it nicely later on?  Or will this make analysis a mess?
    '''
    for k,v in new_conditions:
        request.condition[k] = v
        request[k] = v
    request.condition_id = get_condition(request.condition)
    update_ass(assid=request.assid, condition=request.condition_id)
    debug('Altered assignment %s conditions to %s'
          % (request.assid, request.condition))
    
def alter_price(new_price):
    '''
    This doesn't change the condition recorded in the hit or ass.  It
    just changes the price that we'll be paying people.
    '''
    request.condition['price'] = new_price
    request.price = new_price
    if request.live:
        record_hit_data(request.hitid, price=request.price)


def load_live_hit():
    log('Loading a live hit!')
    if request.vars.live == None: raise Exception('not live')
    if not (request.hitid and db.hits(hitid=request.hitid)):
        raise Exception("This hit %s does not exist in utiliscope database!"
                        % request.hitid)


    # Load hit from the database.  Get the basics.
    hit = db.hits(hitid = request.hitid)
    request.study = db.studies[hit.study]
    if hit.othervars and sj.loads(hit.othervars):
        othervars = sj.loads(hit.othervars)
        request.update(othervars)
        request.vars.update(othervars)
    request.task = hit.controller_func
    # Set up the task options, now that we know the task:
    make_request_vars_convenient() 

    # Now BRANCH.  If this is a preview, show the preview page.
    if is_preview():
        record_action('preview')
        log('this is preview. giving it a preview page.')
        if options['mystery_task']:
            request.controller, request.function = 'utiliscope','preview'
            response.view = '%s/%s.%s' % (request.controller, request.function, 'html')
        # And get outa here!
        return None

    # Else, continue processing the accepted HIT!
    if not (request.workerid and request.assid):
        raise Exception('bad workerid or assid')

    # Load the experimental conditions.
    if not request.study.conditions:
        raise Exception('No conditions for this study')
    request.condition = sample_from_conditions(
        sj.loads(request.study.conditions),
        request.workerid)
    if not request.vars.ajax:
        log('Sampled %s' % request.condition)
    for k,v in request.condition.items():
        request[k] = v
    request.condition_id = get_condition(request.condition)

    # Take note of this assignment.  If it's brand new, fire the "hit
    # accepted" event.
    if not db.assignments(assid=request.assid):
        debug('Worker accepted a fresh hit!')
        record_action('accept')
    update_ass(assid=request.assid,
               hitid=request.hitid,
               workerid=request.workerid,
               status='accepted to us',
               condition=request.condition_id if request.condition_id else None)

    record_action('display', '%s/%s' % (request.controller, request.function))

    # If this worker has passed the work limit, tell them they're done.
    work_limit = request.max_hits or request.work_limit
    if work_limit and hits_done(request.workerid, request.study) >= work_limit:
        request.controller, request.function = 'utiliscope','done'
        response.view = '%s/%s.%s' % (request.controller, request.function, 'html')
        record_action('work quota reached')
        debug('Too many for %s' % request.workerid)
        try:
            turk.expire_hit(request.hitid)
        except TurkAPIError as e:
            logger.error(str(e.value))
        return

    return

def load_testing_hit():
    request.task = task_for(request.controller, request.function)
    # Set up the task options, now that we know the task:
    make_request_vars_convenient() 
    task_options = options[request.task] if \
        request.task in options and isinstance(options[request.task], dict) \
        else {}

    # Load conditions ... in a bunch (too many) of ways
#     if request.vars.condition:
#         request.condition = sj.loads(db.conditions[int(request.vars.condition)].json)

    if is_preview():
        request.condition = {}
        if options['mystery_task']:
            request.controller, request.function = 'utiliscope','preview'
            response.view = '%s/%s.%s' % (request.controller, request.function, 'html')
    else:
        request.condition = {'price' : .03}
        # First set some defaults
        request.condition.update(sample_firsts_from_conditions(task_options))

    # Then override by anything that's been explicitly passed in
    for k,v in task_options.items():
        if k in request.vars:
            # Then look for the value of it in there, and grab that
            request.condition[k] = next(x for x in v if str(x) == request.vars[k])

    # Now make them accessible
    for k,v in request.condition.items():
        request[k] = v
    return

theme = 'white'

# if request.controller == 'appadmin':
#     execfile('applications/utility/models/utiliscope/db.py')
#debug('%s %s %s', request.application, request.controller, request.function)
