# -*- coding: utf-8 -*-
import types

# For debugging database migration files:
#import hashlib
#log('Using db %s %s' % (database, hashlib.md5(database).hexdigest()))


# db.define_table('process_status',
#                 db.Field('name', 'text'),
#                 db.Field('last_seen', 'datetime'),
#                 migrate=migratep, fake_migrate=fake_migratep)

# def heartbeat(process_name):
#     row = db.process_status(name=process_name)
#     if not row: row = db.process_status.insert(name=process_name)
#     row.update_record(last_seen=datetime.now())
#     db.commit()

# Indices:
# hits.{status, launch_date, and hitid (right?)}
# hits_log.{creation_time, hitid}

def create_indices_on_postgres():
    '''Creates a set of indices if they do not exist'''
    ## Edit this list of table columns to index
    ## The format is [('table', 'column')...]
    indices = [('actions', 'study'),
               ('actions', 'assid'),
               ('actions', 'hitid'),
               ('actions', 'time'),
               ('actions', 'workerid'),
               ('countries', 'code'),
               ('continents', 'code'),
               ('hits', 'study'),
               ('ips', 'from_ip'),
               ('ips', 'to_ip'),
               ('workers', 'workerid'),
               ('store', 'key')]
    for table, column in indices:
        index_exists = db.executesql("select count(*) from pg_class where relname='%s_%s_idx';"
                                     % (table, column))[0][0] == 1
        if not index_exists:
            db.executesql('create index %s_%s_idx on %s (%s);'
                          % (table, column, table, column))
        db.commit()


for table in db.tables:
    def first(self):
        return db(self.id>0).select(orderby=self.id, limitby=(0,1)).first()
    def last(self, N=1):
        rows = db(self.id>0).select(orderby=~self.id, limitby=(0,N))
        return rows.first() if N==1 else rows
    def all(self, *cols, **rest):
        return db(self.id>0).select(*cols, **rest)
    def count(self):
        return db(self.id>0).count()
    t = db[table]
    t.first = types.MethodType(first, t)
    t.last = types.MethodType(last, t)
    t.all = types.MethodType(all, t)
    # Count causing an error
    #t.count = types.MethodType(count, t)


# def available_conditions(study):
#     conds = [sj.loads(db.conditions[x.condition].json)
#              for x in
#              db(db.actions.study == study) \
#                  .select(db.actions.condition, distinct=True)]
#     conds = sorted(conds, key=lambda cond: cond['price'])
#     return [get_condition(x) for x in conds]


def available_conditions(study):
    conds = [sj.loads(db.conditions[x.condition].json)
             for x in
             db(db.actions.study == study) \
                 .select(db.actions.condition, distinct=True)]
    vars = experimental_vars(study)
    conds = sorted(conds, key=lambda c: [c['price']] + [c[v] for v in vars if v != 'price'])
    return [get_condition(x) for x in conds]




'''
Also will write something like this:

def get_conditions_space(dict, possibilities):
    json = sj.dumps(dict)
    return get_or_make_one((db.conditions.json == json),
                           db.conditions,
                           {'json' : json})
'''


'''
I want to by syncd on
  - hits that have been launched
  - payments I've made
  - assignments that have been approved or not

Assignment lifecycle:
  1 Accepted by a person
  - "Touched" by worker during work.
  - Returned, timed out, or finished
'''


def clean_bonus_queue(sloppy=False):
    for b in db(db.bonus_queue.id > 0).select():
        turks_ass = turk.get_assignments_for_hit(b.hitid)
        if len(turks_ass) != 1: continue
        turks_ass = turks_ass[0]
        turks_assid = turk.get(turks_ass, 'AssignmentId')
        turks_ass_status = turk.get(turks_ass, 'AssignmentStatus')
        bonus_ass_status = turk.assignment_status(b.assid, b.hitid)
        turk_ass_ok = (turks_ass_status == u'Approved')
        if sloppy:
            turk_ass_ok = turk_ass_ok or (turks_ass_status == u'Submitted')
        if turk_ass_ok \
                and turks_assid != b.assid \
                and not bonus_ass_status:
            # Then the item we have in the bonus queue is no good.
            log('BAD ASS:  %s' % b.assid)
            log('GOOD ASS: %s, %s' % (turks_assid, turks_ass_status))
            del db.bonus_queue[b.id]
        else:
            if turks_assid == b.assid:
                reason = 'the two assids (bonus v. turk) are a MATCH'
            elif bonus_ass_status:
                reason = 'bonus_ass exists with a status of %s' % bonus_ass_status
            elif not (turks_ass_status == u'Approved'
                      or turks_ass_status == u'Submitted'):
                reason = 'turks_ass_status is %s' % turks_ass_status
            else:
                reason = '... er actually we got a bigger problem than that'
            log("..ok cuz " + reason)
    log('#### Run db.commit() now!!!!!!! ####')

def approve_assignment(assid, hitid):
    turk.approve_assignment(assid)
    update_ass_from_mturk(hitid)

def give_bonus_up_to(assid, workerid, bonusamt, reason):
    delta = turk.give_bonus_up_to(assid, workerid, float(bonusamt), reason)
    add_to_ass_paid(assid, delta)

    
def setup_db(study=None, force=False):
    log('Creating postgres indices')
    create_indices_on_postgres()
    load_ip_data(force)
    update_worker_info(force)
    if study:
        log('Populating runs for study %d' % study)
        populate_runs(study)



## ============ maintaining mirror of mturk database ===========

def schedule_hit(launch_date, study, controller_func, othervars):
    def varnum(array, index): return array[index] if len(array) > index else None
    db.hits.insert(status = 'unlaunched',

                   launch_date = launch_date,
                   study = study,
                   controller_func = controller_func,

                   othervars = sj.dumps(othervars)
                   )
    db.commit()



def add_to_ass_paid(assid, amount):
    ass = get_one(db.assignments.assid == assid)
    soft_assert(ass, 'WTF no ass???')
    ass.update_record(paid = float(ass.paid) + float(amount))
    db.commit()


# Tasks
def send_email_task(to, subject, message):
    debug_t('Sending email now from within the scheduler!')
    if True:   # Use sendmail
        SENDMAIL = "/usr/sbin/sendmail" # sendmail location
        import os
        p = os.popen("%s -t" % SENDMAIL, "w")
        p.write("To: " + email_address + "\n")
        p.write("Subject: " + subject + "\n")
        p.write("\n") # blank line separating headers from body
        p.write(message)
        p.write("\n")
        status = p.close()
        if status != 0:
            #print "Sendmail exit status", sts
            pass

    else:   # Use gmail
        from gluon.tools import Mail
        mail = Mail()
        mail.settings.server = 'smtp.gmail.com:587'
        mail.settings.sender = 'mturk@utiliscope.net'
        mail.settings.login = 'mturk@utiliscope.net:byebyesky'
        mail.send(to, subject, message)
    debug_t('Sent!')


def refresh_hit_status():
    hits = db(db.hits.status.belongs(('open', 'getting done'))).select()
    db.rollback()
    failed_refreshes = []
    for hit in hits:
        try:
            xml = turk.get_hit(hit.hitid)
        except TurkAPIError as e:
            failed_refreshes.append(hit.hitid)
            continue

        status = turk.is_valid(xml) and turk.get(xml,'HITStatus')
        if not status:
            continue

        # status starts out as 'open' or 'getting done' and we'll record it as:
        #
        #  [mturk status] -> [what we call it]
        #  Assignable     -> open
        #  Unassignable   -> getting done
        #  Reviewable     -> closed
        #  Reviewing      -> closed

        newstatus = hit.status
        #log("refreshing %s %s" % (hitid, status))
        if status == u'Assignable':
            newstatus = 'open'
        if status == u'Unassignable':
            newstatus = 'getting done'
        elif status == u'Reviewable' or status == u'Reviewing':
            # Unassignable happens when someone is doing it now
            # The only other option is Assignable
            newstatus = 'closed'
        record_hit_data(hitid=hit.hitid, status=newstatus, xmlcache=xml.toxml())
    if failed_refreshes:
        debug_t('MTurk API went bogus for refreshing %s/%s hits',
                len(failed_refreshes), len(hits))

def process_bonus_queue():
    try:
        for row in db().select(db.bonus_queue.ALL):
            #debug_t('Processing bonus queue row %s' % row.id)
            try:
                approve_and_bonus_up_to(row.hitid, row.assid, row.worker, float(row.amount), row.reason)
                debug_t('Success!  Deleting row.')
                db(db.bonus_queue.assid == row.assid).delete()
                if False:
                    worker = db(db.workers.workerid == row.worker).select()[0]
                    worker.update_record(bonus_paid=worker.bonus_paid + float(row.amount))
                db.commit()
            except TurkAPIError as e:
                logger_t.error(str(e.value))
    except KeyboardInterrupt:
        debug_t('Quitting.')
        db.rollback()
        raise
    except Exception as e:
        logger_t.error('BAD EXCEPTION!!! How did this happen? letz rollback and die... ' + str(e))
        try:
            db.rollback()
        except Exception as e:
            logger_t.error('Got an exception handling even THAT exception: ' + str(e.value))
        raise
    #debug('we are done with bonus queue')

def process_launch_queue_task():
    process_launch_queue()

def approve_and_bonus_up_to(hitid, assid, workerid, bonusamt, reason):
    ass_status = turk.assignment_status(assid, hitid)
    debug_t('Approving $%s ass %s of status %s' %
            (bonusamt, assid, ass_status))

    if len(turk.get_assignments_for_hit(hitid)) == 0:
        raise TurkAPIError("...mturk hasn\'t updated their db yet")
        

    # First approve the assignment, but only if it's "submitted"
    if ass_status == u'Submitted':
        turk.approve_assignment(assid)

#     if ass_status == None:
#         log('The XML we are getting for this crapster is %s'
#                       % turk.ask_turk_raw('GetAssignmentsForHIT', {'HITId' : hitid}))

    if turk.assignment_status(assid, hitid) != u'Approved':
        raise TurkAPIError('Trying to bonus a hit that isn\'t ready!  it is %s'
                           % turk.assignment_status(assid, hitid))

    #log('Now it must be approved.  doing bonus of $%s' % bonusamt)

    # Now let's give it a bonus
    if float(bonusamt) == 0.0:
        #log('Oh... nm this is a 0.0 bonus')
        pass
    else:
        turk.give_bonus_up_to(assid, workerid, float(bonusamt), reason)

    # Update the assignment log and verify everything worked
    update_ass_from_mturk(hitid)
    if turk.assignment_status(assid, hitid) != u'Approved' \
            or turk.bonus_total(assid) < float(bonusamt) - .001:
        raise TurkAPIError('Bonus did\'t work! We have %s and %s<%s'
                           % (turk.assignment_status(assid, hitid),
                              turk.bonus_total(assid),
                              float(bonusamt)))

def update_ass_from_mturk(hitid):
    # Get the assignments for this from mturk
    asses = turk.get_assignments_for_hit(hitid)

    # Go through each assignment
    for ass in asses:
        assid = turk.get(ass, 'AssignmentId')
        bonus_amount = turk.bonus_total(assid)

        update_ass(assid,
                   hitid=turk.get(ass, 'HITId'),
                   workerid=turk.get(ass, 'WorkerId'),
                   status=turk.get(ass, 'AssignmentStatus'),
                   paid = bonus_amount,
                   xmlcache=ass.toxml())
    

def process_launch_queue():
    for hit in db((db.hits.status == 'unlaunched')
                  & (db.hits.launch_date < datetime.now())).select():
        if generalp:
            study = get_one(db.studies.id == hit.study)
            params = sj.loads(study.params)
            params['task'] = hit.controller_func
            my_params = make_task_params(**params)
            launch_hit(hit,my_params)
        else:    
            launch_hit(hit, mystery_task_params(hit.controller_func))

# Shortcut functions for turk calls
get_hit = turk.get_hit
get_assignments = turk.get_assignments_for_hit
create_hit = turk.create_hit
dispose_hit = turk.dispose_hit
disable_hit = turk.disable_hit
register_hit_type = turk.register_hit_type
create_hit = turk.create_hit
get_hit_status = turk.get_hit_status
get_bonus_amount = turk.bonus_total
give_bonus_up_to = turk.give_bonus_up_to
give_bonus = turk.give_bonus
message_worker = turk.message_worker
message_workers = turk.message_workers
hit_url = turk.hit_url


def hit_serve_url(controller_and_func):
    url = 'localhost' if (sandbox_serves_from_localhost_p and sandboxp) else server_url
    return 'http://%s:%s/%s?live' % (url, server_port, controller_and_func)
def mystery_task_params(task):
    return Storage(
        {'question' : turk.external_question(hit_serve_url(task),
                                             iframe_height),
         'title' : 'Mystery Task (BONUS)',
         'description' : 'Preview to see the task and how much it pays.  We continually change the payments and tasks for these hits, so check back often.  All payments are in bonus.  You will be paid within minutes of finishing the HIT.',
         'keywords' : 'mystery task, bonus, toomim',
         'ass_duration' : ass_duration,
         'lifetime' : hit_lifetime,
         'assignments' : 1,
         'reward' : 0.0,
         'tag' : None})


def launch_hit(hit, params):
    try:
        # Check db.hits for the hit
        # if it doesn't exist or is launched, throw an error.
        # otherwise, create it and update hits and hits_log

        # Make sure it's fresh (dunno if this actually helps)
        hit = db.hits[hit.id]
        assert hit.status == 'unlaunched', 'Hit is already launched!'

        result = turk.create_hit(params.question,
                                 params.title,
                                 params.description,
                                 params.keywords,
                                 params.ass_duration,
                                 params.lifetime,
                                 params.assignments,
                                 params.reward,
                                 params.tag)

        hitid = turk.get(result, 'HITId')
        if not hitid: raise TurkAPIError('LOST A HIT! This shouldn\'t happen! check this out.')

        debug_t('Launched hit %s' % hitid)

        # Get this into the hits database quick, in case future calls fail
        hit.update_record(hitid=hitid, xmlcache='fail! not inserted yet', status='open')
        db.commit()

        # Now let's get the xml result, and put the rest of this into the log
        xml = turk.get_hit(hitid)
        record_hit_data(hitid=hitid,
                        #creation_time=turk.hit_creation(xml),
                        xmlcache=xml.toxml())

    except TurkAPIError as e:
        debug_t('Pooh! Launching hit id %s failed with:\n\t%s' \
                    % (hit.id, e.value))


# if request.controller not in ['utiliscope'] :
#     Scheduler(db, dict(send_email=send_email_task))



# def fixup_hits_log_old():
#     assert False
#     hits = db(db.hits_log.creation_time == None).select()
#     for hit in hits:
#         if hit.creation_time != None:
#             raise Exception, "foo!"
#         hit.update_record(creation_time=turk.hit_creation(turk.getHit(hit.hitid)))
#         db.commit()
#         print ('done with hit %s/%s %s' % (hit.id, len(hits), hit.hitid))

# def fixup_hits_log():
#     assert False
#     last_hit = db().select(db.hits_log.ALL, limitby=(0,1),
#                            orderby=~db.hits_log.id)[0].id
#     hits = db(db.hits_log.xmlbody == None).select(orderby=db.hits_log.id)
#     for hit in hits:
#         if hit.xmlbody != None:
#             raise Exception, "foo!"
#         xml = turk.get_hit(hit.hitid)
        
#         hit.update_record(xmlbody=xml.toxml(),
#                           creation_time=turk.hit_creation(xml))
#         db.commit()
#         print ('done with hit %s/%s %s' % (hit.id, last_hit, hit.hitid))


# def populate_ass():
#     assert False
#     try:
#         last_hit = db().select(db.hits_log.ALL, limitby=(0,1),
#                                orderby=~db.hits_log.id)[0].id
#         for hit in db(db.hits_log.id > 0).select(orderby=db.hits_log.id):
#             print ('%s / %s' % (hit.id, last_hit))
#             if db(db.assignments.hitid == hit.hitid).count() > 0:
#                 print 'We already did hit %s' % hit.hitid
#             else:
#                 asses = turk.get_assignments_for_hit(hit.hitid)
#                 if len(asses) == 0:
#                     db.assignments.insert(assid='None',
#                                           hitid=hit.hitid)
#                 for ass in asses:
#                     print ('Updating hit %s\'s ass %s'
#                            % (hit.hitid, turk.get(ass, 'AssignmentId')))
#                     db.assignments.insert(assid=turk.get(ass, 'AssignmentId'),
#                                           hitid=turk.get(ass, 'HITId'),
#                                           workerid=turk.get(ass, 'WorkerId'),
#                                           status=turk.get(ass, 'AssignmentStatus'),
#                                           xmlcache=ass.toxml(),
#                                           paid = -1)
#                 db.commit()
#     except:
#         db.rollback()
#         raise

def populate_ass_bonuses():
    query = (db.assignments.paid == -1) & (db.assignments.assid != 'None')
    last_ass = db(query).select(db.assignments.ALL,
                                limitby=(0,1),
                                orderby=~db.assignments.id)[0].id

    for ass in db(query).select(orderby=db.assignments.id):
        bonus = turk.bonus_total(ass.assid)
        print ('%s/%s Bonus for %s is %s'
               % (ass.id, last_ass, ass.assid, bonus))
        ass.update_record(paid = bonus)
        db.commit()

def add_hits_log_creation_dates():
#     for hit in db().select(db.hits_log.ALL):
#         hit.update_record(xmlbody = hit.xmlbody.replace('\n','')
#                           .replace('\t',''),
#                           creation_time)
    pass

def pay_poor_souls():
    poor_souls = db((db.hits_log.creation_time < datetime(2009, 12, 28))
                    & (db.hits_log.creation_time > datetime(2009, 11, 1))
                    & (db.assignments.hitid == db.hits_log.hitid)
                    & (db.assignments.paid == 0)
                    & (db.assignments.assid != 'None')).select(
        orderby=db.hits_log.creation_time)
    for row in poor_souls:
        print row.assignments.assid, row.hits_log.hitid, row.hits_log.creation_time
    print len(poor_souls)

def unpaid_assignments(workerid = None):
    query = (db.assignments.status == 'finished to us')
    if workerid: query = query & (db.assignments.workerid == workerid)
    asses = db(query).select()
    return asses

def pay_unpaid_assignments(workerid = None):
    for ass in unpaid_assignments(workerid):
        if ass.condition:
            price = sj.loads(db.conditions[ass.condition].json)['price']
            assert(is_price(price))
            enqueue_bonus(ass.assid, ass.workerid, ass.hitid, price)

def update_ass_conditions():
    for i,ass in enumerate(db().select(db.assignments.ALL)):
        if ass.assid:
            actions = db(db.actions.assid == ass.assid) \
                .select(db.actions.condition, distinct=True)
            if len(actions) == 1 and actions[0].condition:
                print 'Updating', ass.assid, actions[0].condition
                ass.update_record(condition=actions[0].condition)
            else:
                print 'foo', len(actions), actions[0].condition if len(actions) == 1 else ''

def study_feedback(study):
    return db((db.feedback.hitid == db.hits.hitid)
              & (db.hits.study == study)).select(db.feedback.message,
                                                 db.feedback.time,
                                                 db.hits.hitid,
                                                 db.feedback.workerid,
                                                 orderby=~db.feedback.time)

########################
# Geolocation

def load_ip_data(force=False):
    if db(db.ips.id > 0).count() != 0 and not force:
        log('Already have IP data loaded.')
        return
    else:
        log('Loading IPLocation database')

    db.ips.truncate('cascade')
    db.countries.truncate('cascade') # shouldn't be necessary
    db.continents.truncate('cascade') # but what the hay

    import csv
    with open('../ipligence-community.csv','rb') as f:
        log('Populating continents')
        rows = csv.reader(f)
        for row in rows:
            if not get_one(db.continents.code==row[4]):
                db.continents.insert(code=row[4], name=row[5])
        db.commit()

    with open('../ipligence-community.csv','rb') as f:
        log('Populating countries')
        rows = csv.reader(f)
        for row in rows:
            if not get_one(db.countries.code==row[2]):
                continent = get_one(db.continents.code==row[4])
                db.countries.insert(code=row[2], name=row[3], continent=continent)
        db.commit()

    with open('../ipligence-community.csv','rb') as f:
        log('Populating ips')
        rows = csv.reader(f)
        for row in rows:
            country = get_one(db.countries.code==row[2])
            db.ips.insert(from_ip=row[0], to_ip=row[1], country=country)
        db.commit()

def number_to_ip( intip ):
        octet = ''
        for exp in [3,2,1,0]:
                octet = octet + str(intip / ( 256 ** exp )) + "."
                intip = intip % ( 256 ** exp )
        return(octet.rstrip('.'))

def ip_to_number( dotted_ip ):
        exp = 3
        intip = 0
        for quad in dotted_ip.split('.'):
                intip = intip + (int(quad) * (256 ** exp))
                exp = exp - 1
        return(intip)

def ip_country(ip):
    num = str(ip_to_number(ip))
    rows = db((db.ips.from_ip <= num)
             & (db.ips.to_ip > num)).select()
    if not(len(rows) == 1 and rows[0] and rows[0].country):
        return get_one(db.countries.code == '')
    else:
        return db.countries[rows[0].country]

def worker_country(workerid):
    return db.countries[get_one(db.workers.workerid == workerid).country]

def worker_ip(workerid):
    row = db(db.actions.workerid == workerid).select(db.actions.ip, limitby=(0,1), orderby=~db.actions.time)
    if row and row.ip:
        return row.ip
    else:
        return None

def country_time_zone(country):
    continents = {'NA' : 2,
                  'SA' : 2,
                  'EU' : 9,
                  'CB' : 4,
                  'AF' : 9,
                  'ME' : 10,
                  'CA' : 1,
                  'AS' : 15,
                  'OC' : 17,
                  'COMMUNICAT' : 0,
                  'MEDIA' : 0,
                  '' : 0}

    countries = {'IN' : 12,
                 '' : 0}

    if country.code in countries:
        return countries[country.code]
    elif country.continent.code in continents:
        return continents[country.continent.code]
    

def update_worker_info(force=False):
    rows = db().select(db.actions.workerid, distinct=True)
    if len(rows) > db(db.workers.id>0).count(distinct=db.workers.workerid) \
            and not force:
        log('Already have worker info updated.')
        return
    else:
        log('Updating worker info')

    for i,row in enumerate(rows):
        ip = db(db.actions.workerid == row.workerid).select(limitby=(0,1))[0].ip
        if i % 100 == 0:
            logger.info('updating iteration %s for ip %s' % (i,ip))
        country = ip_country(ip)
        if country.code == '':
            logger.info('No country for IP %s' % ip)
        time_zone = country_time_zone(country) or 0
        update_or_insert_one(db.workers, 'workerid', row.workerid,
                             dict(latest_ip=ip,
                                  country=country,
                                  time_zone=time_zone))
    db.commit()



# ============== Migration Help =============
def db_hash(): 
    import cPickle, hashlib
    return hashlib.md5(database).hexdigest()

def get_migrate_status(table_name):
    import cPickle, hashlib
    f = open('applications/utility/databases/%s_%s.table'
             % (hashlib.md5(database).hexdigest(),
                table_name),
             'r')
    result = cPickle.load(f)
    f.close()
    return result

def save_migrate_status(table_name, status):
    import cPickle, hashlib
    f = open('applications/utility/databases/%s_%s.table'
             % (hashlib.md5(database).hexdigest(),
                table_name),
             'w')
    cPickle.dump(status, f)
    f.close()
    print 'saved'

def del_migrate_column(table_name, column_name):
    a = get_migrate_status(table_name)
    del a[column_name]
    save_migrate_status(table_name, a)


def reload_model(name):
    '''THIS DOES NOT WORK'''
    execfile(request.folder + '/models/' + name + '.py')
    return 'THIS DOES NOT WORK'


## This is kyle's code for quality judgements... unfinished
if False:
    db.define_table('prompt',
                    db.Field('prompt', 'text'),
                    db.Field('example', 'text'),
                    db.Field('study', db.studies),
                    migrate=migratep, fake_migrate=fake_migratep)

    db.define_table('response',
                    db.Field('fkpromptid', db.prompt),
                    db.Field('workerid'),
                    db.Field('assignmentid'),
                    db.Field('response', 'text'),
                    db.Field('labelings', 'integer'), # initially zero, represents amount of times it has been rated
                    db.Field('time', 'datetime'),
                    migrate=migratep, fake_migrate=fake_migratep)

    db.response.assignmentid.requires = [IS_NOT_IN_DB(db,
                                                      db.response.assignmentid),
                                         IS_NOT_EMPTY()]
    db.response.response.requires = IS_NOT_EMPTY()
    db.response.labelings.requires = IS_NOT_EMPTY()

    db.define_table('rating',
                    db.Field('assignmentid'),
                    db.Field('turkerid'),
                    db.Field('fkresponseid', db.response),
                    db.Field('grammar', 'integer'),
                    db.Field('concise', 'integer'),
                    db.Field('coherent', 'integer'),
                    db.Field('relevance', 'integer'),
                    db.Field('interesting', 'integer'),
                    db.Field('time', 'datetime'),
                    migrate=migratep, fake_migrate=fake_migratep)

    db.rating.assignmentid.requires = [IS_NOT_IN_DB(db,
                                                    db.rating.assignmentid),
                                       IS_NOT_EMPTY()]
    db.rating.turkerid.requires = [IS_NOT_IN_DB(db, db.rating.turkerid),
                                   IS_NOT_EMPTY()]
    db.rating.fkresponseid.requires = IS_IN_DB(db, 'response.id')

    db.define_table('result',
                    Field('fkrating', db.rating),
                    migrate=migratep, fake_migrate=fake_migratep),

    db.result.fkrating.requires = IS_IN_DB(db, 'rating.id')

