

# def log_action(action,
#                hit = request.vars.hitId,
#                worker = request.vars.workerId,
#                ass = request.vars.assignmentId,
#                ip = request.env.remote_addr,
#                once_only = False):



# For each IP, record:
    # did it preview but no accept
    # did accept
    # did it finish?  how many?

# All ip addresses 
# select distinct ip, workerid from actions where workerid is not null and study = 'captcha6 0.01 50';


# def calc_study_price(number, start, stop, increment):
#     def arith(start, stop, increment):
#         return sum([x for x in range(start, stop, increment)])
#     return arith(start, stop, increment) * 

def add_turk_fees(hit_price):
    return max(.005, hit_price + hit_price*.1)
def calc_study_price (num_hits, prices):
    min = calc_study_price_min(num_hits, prices)
    max = calc_study_price_max(num_hits, prices)
    mean = sum([add_turk_fees(x) for x in prices]) * (num_hits/len(prices))
    print "Between $%.2f (balanced) and $%.2f (max).  Min is $%.2f." % (mean, max, min)
    #return mean
def calc_study_price_max (num_hits, prices):
    return add_turk_fees(max(prices)) * (num_hits)
def calc_study_price_min (num_hits, prices):
    return add_turk_fees(min(prices)) * (num_hits)


def launch_test_study(task, num_hits=1):
    study_name = 'teststudy %s' % task
    schedule_study(num_hits, task, study_name, "let's see if it fitts'")

def launch_study(num_hits, task, name, description):
    conditions = options[task]
    study = get_or_make_one(db.studies.name == name,
                            db.studies,
                            {'name' : name,
                             'launch_date' : datetime.now(),
                             'description' : description,
                             'controller_func' : task})
    study.update_record(conditions = sj.dumps(conditions, sort_keys=True))
    for i in range(num_hits):
        schedule_hit(datetime.now(), study.id, task, {})
    db.commit()

schedule_test_study = launch_test_study
schedule_study = launch_study

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


# === functions for generalized task creation ===
def make_task_params(task,title,description,keywords,reward,duration=ass_duration,lifetime=hit_lifetime,assignments=1):
    return Storage(
        {'question' : turk.external_question(hit_serve_url(task),
                                            iframe_height),
         'title' : title,
         'description' : description,
         'keywords' : keywords,
         'ass_duration' : duration,
         'lifetime' : lifetime,
         'assignments' : assignments,
         'reward' : reward,
         'tag' : None})

def init_gen_study(task, name, description, conditions, params):
    study = get_or_make_one(db.studies.name == name,
                            db.studies,
                            {'name' : name,
                             'launch_date' : datetime.now(),
                             'description' : description,
                             'controller_func' : task,
                             'params' : sj.dumps(params, sort_keys=True)})
    study.update_record(conditions = sj.dumps(conditions, sort_keys=True))
    options.task = conditions
    db.commit()

# change so that individual hits can use different controllers?
def schedule_gen_hits(study_name,arg_dict_list):
    study = get_one(db.studies.name == study_name)
    for arg_dict in arg_dict_list:
        schedule_hit(now, study.id, study.controller_func, arg_dict)
    

# ==============

def make_mystery_task(controller_and_func, lifetime = hit_lifetime):
        return turk.create_hit(turk.external_question(turk.external_url(controller_and_func),
                                                      iframe_height),
                               'Mystery Task (BONUS)',
                               'Preview to see the task and how much it pays.  We continually change the payments and tasks for these hits, so check back often.  All payments are in bonus.  You will be paid within minutes of finishing the HIT.',
                               'mystery, bonus',
                               ass_duration,
                               lifetime,
                               1,
                               0.0)

def url(f,args=[],vars={}): return URL(r=request,f=f,args=args,vars=vars)

def get_one(query):
    result = db(query).select()
    assert len(result) <= 1, "GAH Get_one called when there's MORE than one!"
    return result[0] if len(result) == 1 else None
        

def get_or_make_one(query, table, default_values):
    result = get_one(query)
    if result:
        return result
    else:
        table.insert(**default_values)
        return get_one(query)
    
def update_or_insert_one(table, column, equalto, values):
    result = get_one(table[column] == equalto)
    if result:
        result.update_record(**values)
    else:
        values[column] = equalto
        table.insert(**values)

def compute_histogram(array):
    result = [0]*(max(array)+1)
    for x in array:
        result[x] += 1
    return result


def print_hits():
    for study in db().select(db.studies.ALL):
        print study.name
        for h in study.hits.select():
            print '   ', h.launch_date, h.status, h.hitid, h.price, h.othervars

def print_studies():
    for study in db().select(db.studies.ALL, orderby=db.studies.id):
        print '%d\t%d\t%s' % (study.id, db(db.hits.study == study).count(), study.name)


def open_hits():
    return db(db.hits.status.belongs(('open', 'getting done'))).select()

def num_open_hits():
    return db((db.hits.status == 'open')
              |(db.hits.status == 'getting done')).count()

def print_open_hits():
    print db((db.hits.status == 'open')
             |(db.hits.status == 'getting done')).select(db.hits.status,
                                                         db.hits.controller_func,
                                                         db.hits.launch_date)

def expire_open_hits():
    bad_count = 0
    hits = open_hits()
    for hit in hits:
        try:
            turk.expire_hit(hit.hitid)
        except:
            bad_count += 1
    print('FAILED to expire %d/%d hits!' % (bad_count, len(hits)))

def cancel_unlaunched_hits():
    n = db(db.hits.status == 'unlaunched').update(status='launch canceled')
    db.commit()
    log('Canceled %s unlaunched hits' % n)


def experimental_vars(study):
    conditions = sj.loads(study.conditions)
    vars = conditions.keys()
    return [x for x in vars if len(conditions[x]) > 1]

def experimental_vars_vals(study):
    conditions = sj.loads(study.conditions)
    for k,v in conditions.items():
        if len(v) < 2:
            del conditions[k]
        else:
            conditions[k] = sorted(v)
    return conditions

last_study = None
last_conditions = None
def study_conditions_with(study, var, val):
    global last_conditions, last_study
    if last_study != study:
        last_study = study
        last_conditions = available_conditions(study)
    return [c for c in last_conditions if sj.loads(c.json)[var] == val]

def study_conditions_by_var(study, var):
    result = {}
    vars_vals = experimental_vars_vals(study)
    for val in vars_vals[var]:
        result[val] = study_conditions_with(study, var, val)
    return result

def conditions_query(table, conditions):
    query = table.id < 0
    for c in conditions:
        query = (query | (table.condition == c))
    return query

def pretty_condition(study, condition):
    c = sj.loads(condition.json)
    items = c.items()
    def pretty(item):
        if item[0] == 'price':
            return '$%.2f' % item[1]
        elif type(item[1]) == type(.234):
            return '%s %.2f' % (item[0], item[1])
        else:
            return '%s %s' % (item[0], item[1])

    evs = set(experimental_vars(study))

    return ', '.join([pretty(i) for i in items if i[0] in evs])

def pretty_int2(x):
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US')
    return locale.format("%d", x, grouping=True)

def pretty_int(x):
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)

def study_result(study, result):
    if not study.results: return ''
    d = sj.loads(study.results)
    if result not in d: return ''
    return d[result]

def cent_workrate(study):
    r = study_result(study, '1cent_workrate')
    if r == '': return r
    else:
        min = '%.0f' % r[0]
        max = '%.0f' % r[1]
        if min == max: return min + ' hits'
        else: return min + '-' + max + ' hits'

def launch_captcha_hit():
    params = mystery_task_params()
    params.question = turk.external_question(hit_serve_url('captcha'), 800)
    result = turk.create_hit(params.question,
                             params.title,
                             params.description,
                             params.keywords,
                             params.ass_duration,
                             params.lifetime,
                             params.assignments,
                             params.reward,
                             params.tag)


def store_get(key):
    r = db(db.store.key==key).select().first()
    return r and sj.loads(r.value)
def store_set(key, value):
    # update_or_insert doesn't work in old web2pys... cause of a bug...
    #return db.store.update_or_insert(key=key, value=sj.dumps(value))
    # So I wrote my own:
    value = sj.dumps(value)
    record = db.store(db.store.key==key)
    return record.update_record(value=value) \
        if record else db.store.insert(key=key, value=value)

def error_tasks(N=10):
    errors = db(db.scheduler_run.status=='FAILED').select(limitby=(0,N),
                                                          orderby=~db.scheduler_run.id)
    for error in errors:
        print error.id, db.scheduler_task[error.scheduler_task].task_name, error.traceback
def open_scheduler_tasks(task_name=None):
    query = db.scheduler_task.status.belongs(('QUEUED',
                                              'ASSIGNED',
                                              'RUNNING',
                                              'ACTIVE'))
    if task_name:
        query &= db.scheduler_task.task_name == task_name
    return db(query).select()
def process_tickets():
    return "NO! Don't use this."

    def get_table_row(table, row_header):
        # Look for the row with `header' in the first string of
        # the first TD of the row
        for row in table.components:
            #print row.components[0].components[0]
            if row.components[0].components[0] == row_header:
                return row #.components[2].components[0].components[0]
        return None

    def get_beautify_key_value(beautify, key):
        r = get_table_row(beautify.components[0], key)
        if r:
            return r.components[2].components[0]
        return None

    def has_live_get_var(error):
        get_vars = get_beautify_key_value(e.snapshot['request'], 'get_vars')
        if not get_vars: return False
        return get_beautify_key_value(get_vars, 'live')
        
    def find_hitid(error):
        get_vars = get_beautify_key_value(error.snapshot['request'], 'get_vars')
        if not get_vars:
            send_me_mail('Crap, no get_vars in this guy!\n\n %s error')
        hitid = get_beautify_key_value(get_vars, 'hitId')
        if not (hitid and len(hitid.components) == 1):
            send_me_mail('Crap, no hitid in this guy!\n\n %s error')
        return hitid.components[0]
    def is_sandbox(error):
        sandboxp = get_beautify_key_value(e.snapshot['request'], 'sandboxp')
        if not sandboxp or 'components' not in sandboxp or len(components) < 1:
            debug_t('This shouldn\'t happen! in process_tickets()')
            return False
        s = sandboxp.components[0]
        if not (s == 'False' or s == 'True'):
            debug_t('This shouldn\'t happen either! in process_tickets()')
            return false
        return s == 'True'

    if True:
        import os, stat, time
        from gluon.restricted import RestrictedError
        path='applications/utility/errors/'

        last_run = store_get('last_process_tickets_time') or 0.3
        this_run = time.time()

        recent_files = [x for x in os.listdir(path)
                        if os.path.getmtime(path + x) > last_run]

        for file in recent_files:
            debug_t('Trying error file %s' % file)
            e=RestrictedError()
            e.load(request, 'utility', file)

            # Ok, let's see if this was a live one
            if has_live_get_var(e) and not is_sandbox(e):
                debug_t('This error has a live!  Dealing with it now.')
                hitid = find_hitid(e)
                url = ('http://%s:%s/admin/default/ticket/utility/%s'
                       % (server_url, server_port, file))
                send_me_mail("There was an error in your mturk study!!!\nGo check it out at %s"
                             % url)
                try:
                    debug_t('Expiring hit %s' % hitid)
                    result = turk.expire_hit(hitid)
                    # result.toprettyxml().replace('\t', '   ')
                    debug_t('Expired this hit.')
                except TurkAPIError as e:
                    debug_t("Couldn't expire it. Maybe it was already done.  Error was: %s"
                            % e)
        store_set('last_process_tickets_time', this_run)
        db.commit()
#     except Exception as e:
#         debug_t('Got error when processing tickets! %s' % e)

# def beautify_table_to_dict(b):
#     from gluon.html import BEAUTIFY
#     for row in b.components[0].components:
#         key = row.components[0].components[0]
#         value = row.components[2].components[0]
#         if isinstance(value, BEAUTIFY):

