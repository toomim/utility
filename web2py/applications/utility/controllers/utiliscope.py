import os

response.generic_patterns += ['worker_ids.json', 'worker_actions.json']

############################################################
####                 Loading hits                       ####
############################################################

def done():
    response.view = 'done.html'
    return {}
def preview():
    #response.view = 'preview.html'
    return {}

def fake_submit_to_turk():
    return {}

def prep_test(as_preview=False):
    toggle_preview_url = URL(r=request,
                             f='test' if as_preview else 'test_preview',
                             vars=request.vars, args=request.args
                             )

    # Make a new url... where we delete 'test/' and replace it with
    # arg0, then we shift the other args into place

    # Go from '/test/controller?blah' to '/controller?blah'
    controller = request.args[0]
    request.args = request.args[1:]
    # If there's anything left in the args, pop into the function
    if request.args:
        function = request.args[0]
        request.args = request.args[1:]
    else:
        function = 'index'

    # Turn on testing
    request.get_vars.testing = request.vars.testing = True

    # Make up an assignment, worker, and hit
    import random
    def randstring(n):
        return ''.join([str(random.randrange(10)) for i in range(n)])
        return ''.join([chr(random.randrange(97,122)) for i in range(n)])
    for id in ['workerId', 'hitId'] + ([] if as_preview else ['assignmentId']):
        request.get_vars[id] = request.vars[id] = \
            request.vars[id] or 'fake-%s-%s' % (id[:-2], randstring(8))

    # Make the new url
    url = URL(r=request, c=controller, f=function,
              args=[], vars=request.get_vars)

    request.task = task_for(controller, function)
    conditions = (request.task in options
                  and isinstance(options[request.task], dict)
                  and options[request.task]) or {}

    return locals()
def test():
    return prep_test(as_preview=False)
def test_preview():
    response.view = '%s/test.html' % request.controller
    return prep_test(as_preview=True)

def sleep():
    import time
    time.sleep(3)
    return 'hello'

work_limit = 200                 # max hits any worker can do per study
def hit():
    if request.vars.testing:
        request.task = request.vars.task

    load_hit()
    

    if not request.testing:
        if is_preview():
            response.view = 'preview.html'
            log_action('preview')
            log('Preview %s!' % request.task)
            return {}

        if db((db.actions.workerid == request.workerid)
              & (db.actions.study == request.study)
              & (db.actions.action == 'finished')).count() > work_limit:
            response.view = 'done.html'
            log_action('work quota reached')
            log('Too many for %s' % request.workerid)
            try:
                turk.expire_hit(request.hitid)
            except TurkAPIError as e:
                logger.error(str(e.value))
            return {}

    if '/' in request.task:
        request.task_controller, request.task_function = request.task.split('/')
    else:
        request.task_controller = 'hits'
        request.task_function = request.task

    response.view = '%s/%s.%s' % (request.task_controller,
                                  request.task_function,
                                  request.extension)
    
    if not os.path.exists(request.folder + '/views/' + response.view):
        response.view = 'generic.html'

    if request.task_controller == 'hits':
        result = globals()[request.task_function]()
    else:
        from gluon.shell import exec_environment 
        #from gluon.compileapp import run_models_in
        controller = exec_environment('%s/controllers/%s.py'
                                      % (request.folder,
                                         request.task_controller),
                                      request=request,
                                      response=response,
                                      session=session)
        #run_models_in(controller)
        controller.is_preview = is_preview
        result = controller[request.task_function]()

    return result


def submit():
    redirect(turk_submit_url())


def hello():
    theme = 'whitepink'
    with open(request.folder + '/views/utiliscope/hello.markmin') as f:
        docs = f.read()
    return locals()

def fail():
    return 1/0
def error():
    ''' If this is ?live and not sandbox, then expire the hit and send
    an email.  Otherwise, show the bug report ticket.
    '''
    import cgi

    stuff = '''
    r.v.ticket %s<br>
    r.v.Requested uri %s<br>
    r.v.Request_url %s<br>
    Requested uri %s<br>
    Request_url %s''' % (request.vars.ticket,
                         request.vars.requested_uri,
                         request.vars.request_url,
                         request.env.request_uri,
                         request.url)
    ticket = request.vars.ticket

    # Emulate the original error code
    response.status = request.vars.code

    # Sanity check
    if not ticket or ticket == 'None':
        debug(stuff)
        return 'Error %s&nbsp;&nbsp;&nbsp;Tell Mike about this.<p><p>%s' % (response.status,
                                                            stuff)

    # Parse the original page's get vars
    s = request.vars.requested_uri.split('?')
    get_vars = len(s) > 1 and cgi.parse_qs(s[1], keep_blank_values=1)

    # If this is a live non-sandbox hit, do stuff
    if get_vars and 'live' in get_vars:
        url = 'http://%s:%s/admin/default/ticket/%s' % (
            server_url, server_port, ticket)
        message = 'There was an error in your mturk study!!!\n' \
                     + 'Go check it out at %s' % url
        debug(message)
        send_me_mail(message)

        # If we've got a hitid, let's expire it
        try: hitid = get_vars['hitId'][0]
        except: hitid = None
        if hitid:
            debug('Expiring hit %s' % hitid)
            try:
                result = turk.expire_hit(hitid)
                debug('Expired this hit.')
            except TurkAPIError as e:
                debug("Couldn't expire it. Maybe it was already done.  Error was: %s" % e)
        else:
            debug('WEIRD!!!!! Bad??!!!! No hit id for this live guy')

        extra = ''
        if request.sandbox:
            extra = '''<div style="background-color: #eee; margin: 50px; padding: 20px">
                         Here's a handy link to the ticket&emdash;note that this only appears on the sandbox:<br><a href="%s">%s</a></div>'''\
                % (url,ticket)

        return 'server error' + extra

#         request.vars.ticket, 1100, 'black', 'BOMB-B.GIF', 1024, 768)
#         request.vars.ticket, 2000, 'white', 'exploding_bomb.gif', 695, 605)
#         request.vars.ticket, 1300, 'white', 'BOMB-W.GIF', 800, 600)

    return dict(ticket=ticket,
                delay=500,
                color='black',
                img='adam-bomb-animated.gif',
                width=200,
                height=200)


############################################################
####           Displaying Database and Queues           ####
############################################################

def dash():
    return dict(theme='black')
def amazon_health():
    rate = int((1.0-turk.error_rate()) * 10)
    if rate <= 8:
        rate = '<span style="font-size: 300px; font-weight:bold; color: #f00;">%s</span>' % rate
    return rate
def add_log_blanks():
    debug('')
    debug('')
    debug('')
    debug_t('')
    debug_t('')
    debug_t('')
    return 'yeah, baby'

def actions_csv():
    return dict(actions=db().select(db.actions.ALL))

def expire_hit():
    turk.expire_hit(request.args[0])
    redirect(URL(r=request, f='index'))
def launch_one_off_hit():
    assert sandboxp == sj.loads(request.vars.sandbox), \
           'You need to reload that webpage, or reset the sandboxp variable!'
    launch_test_study(request.vars.task)
    debug("We added a hit to the launch queue.")
    return 'success'

def background_process_1():
    log('Processing launch queue')
    process_launch_queue()
    if request and request.args and request.args[0] == 'return':
        redirect(URL(r=request, f='index'))
    import threading
    log('In background_process_1, ' + str(threading.activeCount()) \
                  + ' threads are ' \
                  + str(threading.enumerate()))

def background_process_2():
    log('Processing queues')
    process_bonus_queue()
    refresh_hit_status()
    if request and request.args and request.args[0] == 'return':
        redirect(URL(r=request, f='index'))



############################################################
####           Displaying Studies and Results           ####
############################################################


def index():
    checkpoint('/index %s' % request.client)
    session.forget()
    return dict(turk=turk, theme='black')

def paths():
    study_id = request.args[0]
    if "worker" in request.vars:
        worker_id = request.vars["worker"]
    else:
        worker_id = None
    return dict(theme='black', study_id=study_id, worker_id=worker_id)

def worker_ids():
    study_id = request.args[0]
    results = db((db.actions.action == 'accept') & (db.actions.study == study_id)).select(db.actions.workerid, distinct=True)
    worker_ids = [x.workerid for x in results]
    return dict(worker_ids=worker_ids)
    
def worker_actions():
    study_id = request.args[0]
    worker_id = request.vars["worker_id"]
    actions = db((db.actions.workerid==worker_id) & (db.actions.study == study_id)).select(orderby=db.actions.hitid|db.actions.time|db.actions.id)
    return dict(worker_id = worker_id, actions=actions)
    
def dolores():
    import datetime
    indices = {}
    data = {}

    study = (len(request.args)>0) and db.studies[request.args[0]]
    if not study: return 'No study to graph.  Go back and give me one.'

    study_name = study.name
    query = (db.actions.study == study.id)
    if (request.vars.price):
        query = (query
                 & (db.actions.hitid == db.hits.hitid)
                 & (db.hits.price == request.vars.price))

    rows = db(query).select(db.actions.ALL, orderby=db.actions.time, limitby=(0,1))
    if len(rows) == 0:
        return 'Nothing in this actions table'
    first_time = rows[0].time

    pageloaders = len(db(query&(db.actions.action == 'preview')).select(db.actions.ip, distinct=True))
    #displays = db(query&(db.actions.action == 'display')).count()
    accepted_by = len(db(query&(db.actions.action == 'display')).select(db.actions.ip, distinct=True))
    finished_by = len(db(query&(db.actions.action == 'finished')).select(db.actions.ip, distinct=True))
    #finishes = len(db(query&(db.actions.action == 'finished')).select(db.actions.ip, distinct=True))

    num_hits = len(db(query&(db.actions.action == 'finished')).select(db.actions.hitid, distinct=True))

    if accepted_by == 0 or pageloaders == 0:
        return 'No data yet.  Wait a while... so far we have %s previews and %s displays' % (pageloaders,accepted_by)

    total_hours = 0

    time_range = db(db.actions.study == study).select(
        db.actions.time.min(),
        db.actions.time.max())[0]
    time_range = (time_range['MIN(actions.time)'],
                  time_range['MAX(actions.time)'])
    time_length = (time_range[1] - time_range[0]).seconds

    def hours(dt):
        #td = dt - datetime.datetime(2009, 5, 1)
        td = dt - first_time
        return ((td.seconds) / (60.0 * 60.0)) + td.days * 24.0

    for action in ['display', 'finished', 'preview']:
        data[action] = []
        a = action
        for row in db((db.actions.action == a)
                      & query) \
                      .select(orderby=db.actions.time):

            if request.vars.price:
                # If we're indexing on a price, our query becomes a
                # join and we need to explicitly specify the actions
                # table for the following fetches
                row = row.actions

            if not indices.has_key(row.workerid):
                indices[row.workerid] = len(indices)
            data[action].append({'worker' : indices[row.workerid],
                                 'time' : hours(row.time),
                                 'condition' : row.condition})
            total_hours = max(hours(row.time), total_hours)

    if False:
        # Compute work histogram
        querystr = "select ip,count(ip) as count from actions where study = 'captcha7 0.01 50' and action = 'preview' group by ip order by count(ip);"
        workcounts = db.executesql(querystr)
    #     workcounts = [[x['ip'], x['count']] for x in workcounts]
        workcounts = [x['count'] for x in workcounts]

        histogram = compute_histogram(workcounts)
    else:
        histogram = None

    #description = db(db.studies.study = study).select().description

    def available_prices(study):
        return [h.price for h in
                db((db.hits.study == study.id) & (db.hits.price != None)) \
                    .select(db.hits.price, distinct=True, orderby=db.hits.price)]


    example_hit = study.hits.count() > 0 and study.hits.select()[0]

    return dict(study=study,

                example_hit=example_hit,

                data=sj.dumps(data),
                histogram=sj.dumps(histogram),

                pageloaders=pageloaders,
                accepted_by=accepted_by,
                finished_by=finished_by,

                time_range=time_range,

                total_hours=total_hours,
                num_hits=num_hits,
                available_prices=available_prices(study),
                conditions=available_conditions(study)
                )

def view():
    '''
    
    tic 1: Number of previewERs vs. pageloaders
    tic 2: number of finishers
    tic 3: number of 2x finishers
    

    '''
    import datetime

    study = (len(request.args)>0) and db.studies[request.args[0]]
    if not study: return 'No study to graph.  Go back and give me one.'

    time_range = db(db.actions.study == study).select(
        db.actions.time.min(),
        db.actions.time.max())[0]
    time_range = (time_range['MIN(actions.time)'],
                  time_range['MAX(actions.time)'])
    time_length = (time_range[1] - time_range[0]).seconds

    query = (db.actions.study == study.id)
    num_hits_total = len(db(query&(db.actions.action == 'finished')).select(db.actions.hitid, distinct=True))

    study_name = study.name


    time_window = None
    if request.vars.filter_start and request.vars.filter_end:
        filter_start = timedelta(seconds=int(request.vars.filter_start)) + time_range[0]
        filter_end = timedelta(seconds=int(request.vars.filter_end)) + time_range[0]
        time_window = [filter_start, filter_end]

    data = [calc_trickle_curve(study, condition, time_window)
            for condition in available_conditions(study)]
        
    example_hit = study.hits.count() > 0 and study.hits.select()[0]
    conditions = available_conditions(study)
    return dict(data=data,
                num_hits_total=num_hits_total,
                example_hit=example_hit,
                conditions=conditions,
                study=study,
                time_range=time_range,
                time_length=time_length
                )

#     return {'histogram' : histogram,
#             'num_hits' : num_hits,
#             'pageloaders' : pageloaders}

# def view3():
#     '''

#     Get all ips, put in a table.

#     For each, count the number of previews, accepts, previews.

#     Per ip, add up the number of completions we have for each person
#     into a table.

#     '''

#     import datetime
#     indices = {}
#     data = {}

#     study = (len(request.args)>0) and db.studies[request.args[0]]
#     if not study: return 'No study to graph.  Go back and give me one.'

#     study_name = study.name
#     query = (db.actions.study == study.id)
#     if (request.vars.price):
#         query = (query
#                  & (db.actions.hitid == db.hits.hitid)
#                  & (db.hits.price == request.vars.price))

#     rows = db(query).select(db.actions.ALL, orderby=db.actions.time, limitby=(0,1))
#     if len(rows) == 0:
#         return 'Nothing in this actions table'
#     first_time = rows[0].time

#     data = ['previews', 'displays', 'finishes']
#     data = [db(db.actions.study == study.id).select(db.actions.ip.count().with_alias('count'), db.actions.ip, orderby=db.actions.ip, groupby=db.actions.ip

#     previews = db.executesql("select ip, count(*) from actions where action='preview' group by ip order by ip;")
#     displays = db.executesql("select ip, count(*) from actions where action='display' group by ip order by ip;")
#     finishes = db.executesql("select ip, count(*) from actions where action='finished' group by ip order by ip;")

#     return {}

def rates():
    study = (len(request.args)>0) and db.studies[request.args[0]]
    if not study: return 'No study to graph.  Go back and give me one.'

    example_hit = study.hits.count() > 0 and study.hits.select()[0]
    #conditions = [(c.id, c.json) for c in available_conditions(study)]

    data = study_work_rates(study)
    log('data is %s' % data)

    return dict(example_hit=example_hit,
                study=study,
                data=data
                )

def all_rates():
    study = (len(request.args)>0) and db.studies[request.args[0]]
    if not study: return 'No study to graph.  Go back and give me one.'

    example_hit = study.hits.count() > 0 and study.hits.select()[0]
    #conditions = [(c.id, c.json) for c in available_conditions(study)]

    data = study_work_rates_all(study)
    log('data is %s' % data)

    return dict(example_hit=example_hit,
                study=study,
                data=data
                )


def helloo():
    log('Saying HELLLOOOO!')
    return 'Hi there!'
def dispatch():
    return 'This should never be called, cause it will switch out in the dispatch model file.'
