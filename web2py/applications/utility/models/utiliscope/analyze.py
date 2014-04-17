from scipy import array

# ============== Data Analysis =============
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
def compute_histogram(array):
    result = [0]*(max(array)+1)
    for x in array:
        result[x] += 1
    return result


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
    row = db(db.actions.workerid == workerid).select(db.actions.ip, limitby=(0,1), orderby=~db.actions.time).first()
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


# ==========================================================
# ============== Uncategorized Code Dump Below =============
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ============== Uncategorized Code Dump Below =============
# ==========================================================

def available_prices(study):
    return [h.price for h in
            db((db.hits.study == study.id) & (db.hits.price != None)) \
                .select(db.hits.price, distinct=True, orderby=db.hits.price)]

def rev_integrate(list):
    '''Destroys and returns list'''
    list.reverse()
    list = integrate(list)
    list.reverse()
    return list

def integrate(list):
    '''Destroys and returns list'''
    curr_sum = 0
    for i in range(len(list)):
        val = list[i][1]
        list[i] = (int(list[i][0]), int(list[i][1]+curr_sum))
        curr_sum += val
    return list


# def get_plotty_reddy():
#     from scipy import *
#     from pylab import *


def study_stats(study, ignored_workers=[]):
    time_range = db(db.actions.study == study).select(
        db.actions.time.min(),
        db.actions.time.max())[0]
    time_range = (time_range['MIN(actions.time)'],
                  time_range['MAX(actions.time)'])
    time_length = (time_range[1] - time_range[0])

    num_hits_total = len(db((db.actions.study == study.id)
                            &(db.actions.action == 'finished')
                            &(~db.actions.workerid.belongs(ignored_workers)))\
                             .select(db.actions.hitid, distinct=True))

    query = (db.actions.study==study)&(~db.actions.workerid.belongs(ignored_workers))

    hit_times = []
    for row in db(query & (db.actions.action=='finished')).select():
        start = db(query
                   &(db.actions.action=='accept')
                   &(db.actions.assid==row.assid)).select(limitby=(0,1)).first()
        hit_times.append(row.time - start.time)
    median_hit_time = hit_times[len(hit_times)/2]

    return Storage(time_range=time_range,
                   time_length=time_length,
                   median_hit_time=median_hit_time,
                   num_hits_total=num_hits_total)


def plot_trickle_at(study, stats, steps, i):
    step_size = (stats.time_range[1] - stats.time_range[0])/steps
    plt.cla()
    plot_trickle(study, [stats.time_range[0],
                         stats.time_range[0] + (step_size * i)])
    plt.show()

def plot_trickle_over_time(study, numsteps):
    s = study_stats(study)
    step_size = (s.time_range[1] - s.time_range[0])/numsteps
    for i in range(numsteps):
        plt.cla()
        plot_trickle(study, [s.time_range[0],
                             s.time_range[0] + (step_size * i)])
        plt.show()
        import time
        time.sleep(5)

def compute_trickle_animation(study, numsteps):
    stats = study_stats(study)
    step_size = (stats.time_range[1] - stats.time_range[0])/numsteps
    windows = [[stats.time_range[0], stats.time_range[0] + (step_size * i)]
               for i in range(1,numsteps)]
    conditions = available_conditions(study)
    windows = [[array(calc_trickle_curve(study, c, window)['histogram']).T
                for c in conditions]
               for window in windows]

#     def isitcool(x):
#         if x and x.has_key('histogram'):
#             return 'cool'
#         else: return x
#     p = [[isitcool(x) for x in conditions] for conditions in plots]
#     print p

#     plots = [[x['histogram'] for x in conditions if x and x.has_key('histogram')]
#              for conditions in plots]
    return windows
     
def plot_trickle_at2(cache, i):
    plt.cla()
    for c in range(len(cache[0])):
        plt.plot(cache[i][c][0], cache[i][c][1], marker='.')
    plt.draw()

anim_i = 0
def next_plot(cache, reset=False):
    global anim_i
    if reset or anim_i >= len(cache): anim_i = 0
    plot_trickle_at2(cache, anim_i)
    print 'Time %d of %d' % (anim_i, len(cache))
    anim_i += 1

def animate_trickle(cache):
    next_plot(cache, True)
    for i in range(len(cache)-1):
        next_plot(cache)

def plot_trickle(study, time_window=None):
    import matplotlib.pyplot as plt
    for c in available_conditions(study):
        h = calc_trickle_curve(study, c, time_window)
        if not h: continue
        h = h['histogram']
        plt.plot([x[0] for x in h], [x[1] for x in h], marker='.')

def calc_trickle_curve(study, condition, time_window=None, log=False, as_percents=True):
    query = ((db.actions.study == study.id)
             & (db.actions.condition == condition))

    filter = "actions.action='finished'"
    filter += (" and actions.study=%d and actions.condition=%d"
               % (study.id, condition.id))


    if time_window:
#         log('Plotting actions from %s to %s'
#                       % (time_window[0].isoformat(), time_window[1].isoformat()))

        query = (query
                 & (db.actions.time > time_window[0])
                 & (db.actions.time < time_window[1]))

        filter += " and actions.time > '%s' and actions.time < '%s' " \
            % (time_window[0].isoformat(), time_window[1].isoformat())

    num_hits = len(db(query&(db.actions.action == 'finished'))
                   .select(db.actions.hitid, distinct=True))
    pageloaders = len(db(query&(db.actions.action == 'display'))
                      .select(db.actions.workerid, distinct=True))

    #pageloaders -= duplicates(study, condition)

    if pageloaders == 0:
        histogram = [[0,0]]
    else:
        # What this SQL does:
        #  - Get the number of completions per Workerid
        #  - Count the number of people with each number of completions
        # 
        # Then you have a histogram of the number of people with each
        # number of completions.  Then I'll integrate this from small to
        # high and I get the number of completions trickling down.

        finishers = db.executesql("""select completions,count(*) as workers from
                                         (select actions.workerid,count(*) as completions
                                          from actions
                                          where %s 
                                          group by actions.workerid order by count(*)
                                         ) as foo
                                  group by completions;"""
                                       % filter)
        finishers = rev_integrate(finishers)
        histogram = [[0.0 if as_percents else 0, pageloaders]]
        histogram.extend(finishers)
        if as_percents:
            histogram = [[float(x[0]), (float(x[1]/float(pageloaders)
                                              * 100.0))
                          ] for x in histogram]
        else:
            histogram = [[int(x[0]), int(x[1])] for x in histogram]

        if False:
            endpoint = 175
            histogram = [x for x in histogram if x[0] < 75]
            histogram.append([75,histogram[-1][1]])

    #log=True
    if log:
        import math
        histogram = [[#x[0],
                      math.log(x[0]+1),
                      math.log(x[1]+1)
                      #x[1]
                      ] for x in histogram]

    return {'condition' : '%s' % pretty_condition(study, condition),
            'histogram' : histogram,
            'num_hits' : num_hits,
            'pageloaders' : pageloaders}


def calc_trickle_curve_legacy(study, condition, time_window=None, log=False, as_percents=True):
    '''Good for study 26'''
    if False:
        query = ((db.actions.study == study.id)
                 & (db.actions.condition == condition))

        filter = "actions.action='finished'"
        filter += (" and actions.study=%d and actions.condition=%d"
                   % (study.id, condition.id))
    else:
        query = ((db.actions.condition == condition))

        filter = "actions.action='finished'"
        filter += (" and actions.condition=%d"
                   % (condition.id))


    if time_window:
#         log('Plotting actions from %s to %s'
#                       % (time_window[0].isoformat(), time_window[1].isoformat()))

        query = (query
                 & (db.actions.time > time_window[0])
                 & (db.actions.time < time_window[1]))

        filter += " and actions.time > '%s' and actions.time < '%s' " \
            % (time_window[0].isoformat(), time_window[1].isoformat())

    num_hits = len(db(query&(db.actions.action == 'finished'))
                   .select(db.actions.hitid, distinct=True))
    pageloaders = len(db(query&(db.actions.action == 'display'))
                      .select(db.actions.workerid, distinct=True))

    pageloaders -= duplicates(study, condition)

    if pageloaders == 0:
        histogram = [[0,0]]
    else:
        # What this SQL does:
        #  - Get the number of completions per Workerid
        #  - Count the number of people with each number of completions
        # 
        # Then you have a histogram of the number of people with each
        # number of completions.  Then I'll integrate this from small to
        # high and I get the number of completions trickling down.

        finishers = db.executesql("""select completions,count(*) as workers from
                                         (select actions.workerid,count(*) as completions
                                          from actions
                                          where %s 
                                          group by actions.workerid order by count(*)
                                         ) as foo
                                  group by completions;"""
                                       % filter)
        finishers = rev_integrate(finishers)
        histogram = [[0.0 if as_percents else 0, pageloaders]]
        histogram.extend(finishers)
        if as_percents:
            histogram = [[float(x[0]), (float(x[1]/float(pageloaders)
                                              * 100.0))
                          ] for x in histogram]
        else:
            histogram = [[int(x[0]), int(x[1])] for x in histogram]

        if False:
            endpoint = 175
            histogram = [x for x in histogram if x[0] < 75]
            histogram.append([75,histogram[-1][1]])

    #log=True
    if log:
        import math
        histogram = [[#x[0],
                      math.log(x[0]+1),
                      math.log(x[1]+1)
                      #x[1]
                      ] for x in histogram]

    return {'condition' : '%s' % pretty_condition(study, condition),
            'histogram' : histogram,
            'num_hits' : num_hits,
            'pageloaders' : pageloaders}


def calc_trickle2(study, condition, time_window=None):
    '''Good for matplotlib'''
    return array(calc_trickle_curve(study,condition,time_window,log=False)['histogram']).T

def censored_workers(study, condition):
    def extract_deadzone(row, study):
        return (row.start_time \
                    or db(db.actions.study == study) \
                    .select(db.actions.time.min())[0]['MIN(actions.time)'],
                row.end_time \
                    or db(db.actions.study == study) \
                    .select(db.actions.time.max())[0]['MAX(actions.time)'])

    deadz = db(db.dead_zones.study == study).select()
    deadz = [extract_deadzone(row, study) for row in deadz]

    if len(deadz) == 0: return None

    query = ((db.actions.study == study)
             & (db.actions.condition == condition)
             & (db.actions.action != 'preview'))

    if True:
        assert(len(deadz) == 1)
        zone = deadz[0]
        subq = ((db.actions.time >= zone[0])
                & (db.actions.time <= zone[1]))
    else:
        subq = (db.actions.id < 0)  # false
        for zone in deadz:
            subq = (subq
                    | ((db.actions.time >= zone[0])
                        & (db.actions.time <= zone[1])))

    return db(query & subq).select(db.actions.workerid, distinct=True)

def calc_hazard(study, condition):
    if True:
        query = ((db.actions.study == study.id)
                 & (db.actions.condition == condition))

        filter = "actions.action='finished'"
        filter += (" and actions.study=%d and actions.condition=%d"
                   % (study.id, condition.id))
    else:
        query = ((db.actions.condition == condition))

        filter = "actions.action='finished'"
        filter += (" and actions.condition=%d"
                   % (condition.id))

    finishers = db.executesql("""select completions,count(*) as workers from
                                         (select actions.workerid,count(*) as completions
                                          from actions
                                          where %s 
                                          group by actions.workerid order by count(*)
                                         ) as foo
                                  group by completions;"""
                              % filter)
    



def to_csv_schema(datas):
    '''Good for dycharts'''
    datas = [x['histogram'] for x in datas]
    for x in datas: x.append([x[-1][0] + 1, 0])
    datas = [[[x[0], x[1]] for x in data]
             for data in datas]
    dicts = [dict(d) for d in datas]
    num_datums = max([max(d) for d in dicts])
    result = [[None] * len(datas) for x in range(num_datums)]

    last_vals = [100] * len(datas)

    for i in range(num_datums):
        for j,d in enumerate(dicts):
            if d.has_key(i):
                result[i][j] = d[i]
                last_vals[j] = d[i]
            else:
                result[i][j] = last_vals[j]

    return result

def to_csv(datas):
    result = "Tasks,"
    for j,d in enumerate(datas):
        result += str(d['condition']).replace('"','').replace(',','') + ','
    result = result[0:-1]
    result += '\\n'

#    for i,row in enumerate(divisions(to_csv_schema(datas))):
    for i,row in enumerate(to_csv_schema(datas)):
        result += str(i) + ','
        for j,d in enumerate(row):
            outof = datas[j]['pageloaders']

            if False:
                err = error_bar2(int(d / 100.0 * outof), outof) / float(outof) * 100.0
                result += str(d) + ',' + str(err) + ','
            else:
                result += '%d/%d,' % (d, outof)
        result = result[0:-1]
        result += '\\n'

    return result
def csv_trickles(study):
    data = [calc_trickle_curve(study, condition, as_percents=False)
            for condition in available_conditions(study)]
    return to_csv(data)
def csv_trickles_legacy(study):
    data = [calc_trickle_curve_legacy(study, condition, as_percents=False)
            for condition in available_conditions(study)]
    return to_csv(data)


def divisions(csv_data):
    #log(csv_data)
    return [[float(x[1]) / x[0], float(x[3]) / x[2],
             float(x[2]) / x[0], float(x[3]) / x[1]]
            for x in csv_data if min(x) > 0]

def integrate_trickle_curve(study, condition, time_window):
    from scipy import interpolate
    f = interpolate.interp1d(*calc_trickle2(study,condition))
    from scipy.integrate import quad
    return quad(f, time_window[0], time_window[1])[0]

def trickle_integrals(study, time_window):
    return [(integrate_trickle_curve(study, condition, time_window), condition.json)
            for condition in available_conditions(study)]
def print_integrals(study, time_window):
    ints = [(integrate_trickle_curve(study, condition, time_window), condition)
             for condition in available_conditions(study)]
    for int in ints:
        print int[0], int[1].json

    print 'Differences:'
    for i in range(len(ints)-1):
        print '%d between %d,%d' % ((ints[i+1][0] - ints[i][0]), i,i+1)

def plot_integrals(study, time_window):
    a = trickle_integrals(study, time_window)
    plt.cla()
    plt.plot([x[0] for x in a], '.')
    ax = list(plt.axis())
    ax[0] = 0
    ax[2] = 0
    plt.axis(ax)

def integ(x,tck,constant=-1):
    import numpy as np
    x = np.atleast_1d(x)
    out = np.zeros(x.shape, dtype=x.dtype)
    for n in xrange(len(out)):
        out[n] = interpolate.splint(0,x[n],tck)
    out += constant
    return out

def work_histogram(study, bins=100, conditions=False):
    plt.cla()

    if conditions:
        conditions = [str(x.id) for x in available_conditions(study)]
    else:
        conditions = [' actions.condition ']

    for c in conditions:
        hist = db.executesql("select actions.ip, count(*) as completions from actions where actions.study = %d and actions.action='finished' and actions.condition=%s group by actions.ip order by count(*)" % (study.id, c))

        work = [x[1] for x in hist]
        n, bins, patches = plt.hist(work, bins, range=(1, 100), normed=True, alpha=.5)



def get_medians(study):
    return [get_median(study, c) for c in available_conditions(study)]
def get_median(study, condition):
    rows = db.executesql("select actions.workerid,count(*) as completions from actions where actions.study=%d and actions.action='finished' and actions.condition=%d group by actions.workerid order by count(*)" % (study.id, condition.id))
    return int(rows[len(rows)/2][1])


def prob_greater_than(k, n, p):
    from scipy.stats.distributions import binom
    return sum([binom.pmf(x, n, p) for x in range(k, n+1)])

def prob_less_than(k, n, p):
    from scipy.stats.distributions import binom
    return sum([binom.pmf(x, n, p) for x in range(0, k)])

def error_bar(goods, outof):
    from math import sqrt
    def bi_variance(n,p):
        return float(n) * p * (1.0-p)
    return sqrt(bi_variance(outof, float(goods)/float(outof)))

def error_bar2(goods, outof):
    x = 1
    return error_bar(goods * x, outof * x) / x


def duplicity(study):
    workerids = int(db.executesql("select count(distinct workerid) from actions where study = %d and action = 'display'" % study.id)[0][0])
    ips = int(db.executesql("select count(distinct ip) from actions where study = %d and action = 'display'" % study.id)[0][0])
    return float(ips)/float(workerids)

def duplicates(study=None, condition=None):
    '''
    Returns data in the form [(condition, num duplicates), (..)...]

    Or if you give it a condition, it'll just return that number.

    This is the number of duplicate IPs for ip addresses who we have workerids for.
    '''
    if not study:
        return db.executesql("select cast(count(distinct ip) as float) - cast(count(distinct workerid) as float) as duplicates from actions where action = 'display' and condition=%d" % (condition.id))[0][0]


    if condition:
        return db.executesql("select cast(count(distinct ip) as float) - cast(count(distinct workerid) as float) as duplicates from actions where study = %d and action = 'display' and condition=%d" % (study.id, condition.id))[0][0]
    else:
        return db.executesql("select condition,cast(count(distinct ip) as float) - cast(count(distinct workerid) as float) as duplicates from actions where study = %d and action = 'display' group by condition" % study.id)

def duplicates2(condition):
    '''
    This is the number of duplicate IPs for ip addresses who we have workerids for.
    '''
    return db.executesql("select cast(count(distinct ip) as float) - cast(count(distinct workerid) as float) as duplicates from actions where action = 'display' and condition=%d" % (condition.id))[0][0]


def gap_size():
    return timedelta(minutes=30) # maximum amount of time before we count a new run

def count_run_links(study, spacing):
    workers = [row.workerid for row in
               db((db.actions.action == 'finished')
                  & (db.actions.study == study)) \
                   .select(db.actions.workerid, distinct=True, limitby=(0,50))]
    count = 0
    for worker in workers:
        subcount = 0
        finishes = db((db.actions.action == 'finished')
                      & (db.actions.study == study)
                      & (db.actions.workerid == worker)) \
                      .select(db.actions.ALL, orderby=db.actions.time, limitby=(0,80))
        last = None
        for finish in finishes:
            if last and (last.time + spacing > finish.time):
                count += 1
                subcount += 1
            last = finish
        #print '%d links for worker %s' % (subcount, worker)
    return count

def try_some_spacings(spacings_in_seconds):
    for space in spacings_in_seconds:
        print space, count_run_links(db.studies[26], timedelta(seconds=space))

def populate_runs(study):
    ''' This used to split runs into multiple runs if more than gap
    size had transpired in between hit completions.  I removed that
    feature.'''

    ## TEMPORARY -- CHANGE THIS BACK
    #
    # Each study from now on has an 'accept' event, but some old
    # studies I am analyzing only have 'display' events.  These
    # produce the same result, but 'accept' is more logical.  As soon
    # as I'm done analyzing those studies, let's change this all to
    # 'accept' instead of 'display'.
    accept = 'display'

    db(db.runs.study == study).delete()

    workers = [row.workerid for row in
               db((db.actions.action == accept)
                  & (db.actions.study == study)) \
                   .select(db.actions.workerid, distinct=True)]

    if 'bad_workers' in globals():
        workers = [w for w in workers if w not in bad_workers]

    for worker in workers:
        finishes = db((db.actions.action == 'finished')
                      & (db.actions.study == study)
                      & (db.actions.workerid == worker)) \
                      .select(orderby=db.actions.time)
        first_accept = db((db.actions.action == accept)
                          &(db.actions.workerid == worker)
                          &(db.actions.study == study)) \
                          .select(orderby=db.actions.time,
                                  limitby=(0,1))[0]

        censored = 0 < db((db.actions.action=='work quota reached')
                          & (db.actions.workerid == worker)
                          & (db.actions.study == study)).count()

        run = Storage(workerid=worker,
                      length=len(finishes),
                      study=study,
                      start_time=first_accept.time,
                      end_time=((finishes.last() and finishes.last().time)
                                or first_accept.time),
                      condition=first_accept.condition,
                      censored=censored)

        # Write out the run
        db.runs.insert(**run)

    # Now mark the last runs as censored
    db((db.runs.study==study)
       &(db.runs.end_time > 
         db(db.runs.study==study).select(db.runs.end_time,
                                         orderby=~db.runs.end_time,
                                         limitby=(0,1)).first().end_time
         - gap_size())).update(censored=True)

    db.commit()




def annotate_censored_runs_old_and_powerful(study):
    study_die_time = auto_guess_study_die_time(study)
    buffer = gap_size()
    for run in db(db.runs.study == study).select():
        # A run can be censored cause we ran out of hits
        is_censored = run.end_time > study_die_time # auto dead zone
        dead_zone_matches = db((db.dead_zones.study == study) # manual zones
                               & (db.dead_zones.start_time < run.end_time)
                               & ((db.dead_zones.end_time  > run.end_time)
                                  | (db.dead_zones.end_time == None))).count()
        is_censored = is_censored or dead_zone_matches

        # Or cause the worker exceeded quota
        quota_exceededs = \
            db((db.actions.action == 'work quota reached')
               & (db.actions.study == study)
               & (db.actions.workerid == run.workerid)
               & (db.actions.time > run.end_time)
               & (db.actions.time < (run.end_time + buffer))).count()
        is_censored = is_censored or quota_exceededs > 0
        if is_censored:
            run.update_record(censored=True)

    db.commit()
def auto_guess_study_die_time(study):
    '''Returns the time of the 250th-from-last hit'''
    rows = db((db.actions.study == study)
              & (db.actions.action == 'finished')) \
              .select(db.actions.time,
                      orderby=~db.actions.time,
                      limitby=(0,270))
    return rows[-1].time

def continuize_0(points, to_length):
    '''Adds trailing zeros to fill to_length'''
    points = points + [[points[-1][0] + 1, 0]]
    return continuize(points, to_length)
def continuize(points, to_length):
    points = [[x[0], x[1]] for x in points]
    points = dict(points)
    result = []
    last_val = None
    for i in range(to_length):
        if i in points:
            last_val = points[i]
        result.append(last_val)
    return result


def runs_trickle(condition, censored_only=False, study=None):
    shim = " and censored = 'T' " if censored_only else " and censored = 'F' "
    if study:
        shim += ' and study = %d ' % study.id

    finishers = db.executesql("""select length, count(*) from runs where condition = %d %s group by length order by length"""
                              % (condition.id, shim))
    finishers = integrate(finishers) if censored_only else rev_integrate(finishers)
    
    query = ((db.actions.condition == condition)
             &(db.actions.action == 'display'))
    if study:
        query = query & (db.actions.study == study)

    pageloaders = len(db(query)
                      .select(db.actions.workerid, distinct=True))
#     pageloaders = len(db((db.actions.condition == condition)
#                          &(db.actions.action == 'preview'))
#                       .select(db.actions.ip, distinct=True))
#     pageloaders -= duplicates(condition=condition)

    if False: pageloaders = finishers[0][1] # Don't trust pageloaders now

    result = [[0, pageloaders]]
    result.extend(finishers)

    return result

def runs_csv(conditions, study=None):
    if study:
        if db(db.runs.study == study).count() == 0:
            return 'nothing'

    result = "Tasks,"
    for j,d in enumerate(conditions):
        result += 'Condition ' + str(d.json).replace('"','').replace(',','') + ','
    result = result[0:-1] + '\\n' # Drop last comma, add newline

    datas = [runs_trickle(c, study=study) for c in conditions]
    censored = [runs_trickle(c, True, study=study) for c in conditions]
    for c in censored: c[0] = (0,0)

    length = max([d[-1][0] for d in datas])

    datas = [continuize_0(d, length) for d in datas]
    censored = [continuize(d, length) for d in censored]
    
    def foo(d):
        if len(d) > 0:
            return d[0]
        else:
            return 0.0
    pageloaders = [foo(d) for d in datas]
    outofs = [array([p]*length) - array([0] + c[:-1])
              for p,c in zip(pageloaders,censored)]

#     for d,o in zip(datas[0], list(outofs)[0]):
#         print d,o

    for i in range(length):
        result += str(i) + ','
        for j in range(len(conditions)):
            value = datas[j][i]
            outof = datas[j][0]
            outof = outofs[j][i]
            result += '%d/%d,' % (value, outof)
        result = result[0:-1] + '\\n' # Drop last comma, add newline
    return result

def study_runs_csv(study, filename=None):
    conditions = sj.loads(study.conditions)
    with open(filename or 'study_%d.csv' % study.id, 'w') as f:
        variables = experimental_vars(study)
        f.write('id,run_length,%s,start_time,end_time,workerid,censored,other\n'
                % ','.join(variables))
        for run in db(db.runs.study==study).select():
            condition = sj.loads(run.condition.json)
            vals = ([run.id,
                     run.length]
                    + [condition[key] for key in variables]
                    + [run.start_time,
                       run.end_time,
                       run.workerid,
                       run.censored,
                       run.other])
            f.write(','.join([str(x) for x in vals]) + '\n')
    return 'done'

def rt_ratio1(condition):
    rt = runs_trickle(condition)
    return float(rt[0][1]) / float(rt[1][1])


def work_rate_legacy(conditions):
    query = db.actions.id < 0
    for c in conditions:
        query = (query | (db.actions.condition == c))

    num_hits = len(db(query&(db.actions.action == 'finished'))
                   .select(db.actions.hitid, distinct=True))
    pageloaders = len(db(query&(db.actions.action == 'display'))
                      .select(db.actions.workerid, distinct=True))
    return float(num_hits)/float(pageloaders)

def work_rate(study, conditions, ignored_workers=[]):
    if study.id == 26: return work_rate_legacy(conditions)

    query = db.actions.id < 0
    for c in conditions:
        query = (query | (db.actions.condition == c))

    query = (query) & (db.actions.study == study.id) \
        & (~db.actions.workerid.belongs(ignored_workers))

    num_hits = len(db(query&(db.actions.action == 'finished'))
                   .select(db.actions.hitid, distinct=True))
    pageloaders = len(db(query&(db.actions.action == 'display'))
                      .select(db.actions.workerid, distinct=True))
    if pageloaders == 0: return 0
    return float(num_hits)/float(pageloaders)

def study_work_rates(study, ignored_workers=[]):
    conditions = available_conditions(study)
    condition_specs = sj.loads(study.conditions)
    evs = experimental_vars_vals(study)

    data = []
    for var,vals in evs.items():
        var_data = []
        # for each value, get the conditions with that value, put them into a graph
        for val in vals:
            rate = work_rate(study,
                             study_conditions_with(study, var, val),
                             ignored_workers)
#                              [c for c in available_conditions(study)
#                               if sj.loads(c.json)[var] == val])
            var_data.append((val,rate))
        data.append((var,var_data))
        # and/or maybe to get the mean of all conditions with that value
    return data

def study_work_rates_all(study):
    conditions = available_conditions(study)
    condition_specs = sj.loads(study.conditions)
    evs = experimental_vars_vals(study)

    data = []
    for var,vals in evs.items():
        var_data = []
        # for each value, get the conditions with that value, put them into a graph
        for val in vals:
            rates = [work_rate(study,[c])
                     for c in conditions
                     if sj.loads(c.json)[var] == val]
            var_data.append((val,rates))
        data.append((var,var_data))
        # and/or maybe to get the mean of all conditions with that value

    return data

def study_work_rates_range(study):
    rates = study_work_rates_all(study)
    tmp = []
    for r in rates[0][1]:
        tmp.extend(r[1])
    return (min(tmp), max(tmp))

def study_work_rates_range_1cent(study):
    rates = dict(study_work_rates_all(study))
    if 'price' not in rates \
            or .01 not in dict(rates['price']):
        return study_work_rates_range(study)
    else:
        rates = dict(rates['price'])[.01]
        return (min(rates), max(rates))


def normalize_condition(var, val):
    import math
    if var == 'price':
        return math.log(val + 1.0)
    elif var == 'width':
        return math.log(val/500.0 + 1.0)
    return val

def regress_wr(work_rates):
    from scipy import stats
    result = []
    for var in work_rates:
        arr = array(var[1]).T
        x = arr[0]
        y = arr[1]
        y = array([float(Y) for Y in y])
        x = array([normalize_condition(var[0], X) for X in x])
        x = array(range(len(x)))
        log('%s %s %s' % (var[0], x, y))
        (a,b,r,tt,stderr) = stats.linregress(x, y)

        data = dict(a=a, b=b, stderr=stderr)
        result.append((var[0], data))

    return result

def work_ratio(regression_data):
    data = regression_data
    #log('%s' % regression_data)
    if data[0][0] == 'price':
        ratio = data[1][1]['a'] / data[0][1]['a']
    else:
        ratio = data[0][1]['a'] / data[1][1]['a']
    return abs(ratio)

def wr_3dplot(study):
    data = study_work_rates_all(study)
    rates = data[0][1]
    X = array([range(3)]*3)
    Y = X.T
    Z = array([rates[0][1], rates[1][1], rates[2][1]])

    import numpy as np
    from mpl_toolkits.mplot3d import axes3d
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = axes3d.Axes3D(fig)
    #X,Y,Z = axes3d.get_test_data(0.05)
    ax.contourf3D(X,Y,Z)
    #ax.plot_wireframe(X,Y,Z, rstride=.43, cstride=.2)
    plt.show()

def record_result(study, tag, result):
    if study.results:
        results = sj.loads(study.results)
    else:
        results = {}

    results[tag] = result
    study.update_record(results=results)
    db.commit()

def update_study_results(study):
    record_result(study,
                  '1cent_workrate',
                  study_work_rates_range_1cent(study))

#     record_result(study,
#                   'money_metric',
#                   work_ratio(regress_wr(study_work_rates(db.studies[26])))


def study_expense(study):
    total = 0
    for price,conditions in study_conditions_by_var(study, 'price').items():
        count = db((db.actions.action == 'finished')
                   & (db.actions.study == study)
                   & conditions_query(db.actions, conditions)).count()
        if price * .1 < .005:
            price = price + .005
        else:
            price = price + (price * .1)
        total += count * price
    return total


def quit_times(study, var):
    result = {}
    for val, conditions in study_conditions_by_var(study, var).items():
        query = conditions_query(db.runs, conditions)
        rows = db((db.runs.study == study)
                  & query) \
                  .select('start_time', 'end_time', 'length',
                          orderby='length')

        seconds = 0
        count = 0
        cutoff = -len(rows)/2
        log('Doing %s/%s rows for %s' \
                          % (len(rows)+cutoff,
                             len(rows),
                             val))
        for row in rows[0:cutoff]:
            if True or row['length'] <= 50:
                count += 1
                seconds += (row['end_time'] - row['start_time']).seconds
        result[val] = float(seconds)/count
    return result

# def completion_times(study):
#     workers = [row.workerid for row in
#                db((db.actions.action == 'finished')
#                   & (db.actions.study == study)) \
#                    .select(db.actions.workerid, distinct=True)]
#     for worker in workers:
#         finishes = db((db.actions.action == 'finished')
#                       & (db.actions.study == study)
#                       & (db.actions.workerid == worker)) \
#                       .select(db.actions.time, orderby=db.actions.time)
#         times = []
#         last_finish = None
#         for finish in finishes:
#             if not run:         # if first time seeing this worker's finish
#                 run =  {'workerid': worker,
#                         'length': 1,
#                         'study': study,
#                         'condition': finish.condition}
#                 run['start_time'] = db((db.actions.assid == finish.assid)) \
#                     .select(db.actions.time, orderby=db.actions.time, limitby=(0,1))[0]['time']

#             if last_finish:
#                 if last_finish.time + spacing > finish.time \
#                         and finish.condition == run['condition']:
#                     run['length'] += 1

#                     if finish.condition != run['condition']:
#                         print ('s%d worker %s\'s run switches condition at %s'
#                                % (study, worker, finish.time))
#                 else:
#                     # Wrap it up
#                     run['end_time'] = finish.time
#                     db.runs.insert(**run)
#                     run = None

#                     # Notify me of crap if there's crap
#                     if last_finish.time + spacing > finish.time:
#                         print ('s%d worker %s\'s run switches condition at %s'
#                                % (study, worker, finish.time))
                        
#             last_finish = finish

#         if run: 
#             run['end_time'] = last_finish.time
#             db.runs.insert(**run)
#             run = None

#     db.commit()
    

# #######################

def completion_time(row):
    def total_seconds(timedelta):
        return timedelta.days * 3600 * 24 + timedelta.seconds + timedelta.microseconds / 100000.0
    def total_hours(timedelta):
        return total_seconds(timedelta) / (60 * 60)
    return total_hours(row.runs.end_time - row.runs.start_time)
def completion_rate(row):
    return float(row.runs.length) / completion_time(row)
def wage(row):
    price = sj.loads(row.conditions.json)['price']
    num_tasks = row.runs.length
    return '%.2f' % ((price*num_tasks) / completion_time(row))

def claus_csv(study, extra_cols=None, extra_cols_generators=None):
    import re
    table_field = re.compile('[\w_]+\.[\w_]+')
    null='<NULL>'
    import csv
    with open('study_%d.csv' % study.id, 'w') as file:
        runs = db((db.runs.study == study)
                  & (db.runs.bad != True)
                  & (db.workers.workerid == db.runs.workerid)
                  & (db.countries.id == db.workers.country)
                  & (db.conditions.id == db.runs.condition)) \
                  .select(db.runs.workerid,
                          db.runs.length,
                          db.runs.censored,
                          db.runs.start_time,
                          db.runs.end_time,
                          db.countries.name,
                          db.workers.time_zone,
                          db.runs.condition,
                          db.conditions.json,
                          db.runs.other)

        if (extra_cols==None):
            other = runs[0].runs.other
            d = other and sj.loads(other)
            if isinstance(d,dict) and len(d.keys()) > 0:
                extra_cols = d.keys()
            else:
                extra_cols = []
        if (extra_cols_generators==None):
            # Default generator just looks up the value of the
            # extra_col inside the row's "other" field's json object
            def f(col):
                def g(row):
                    return sj.loads(row.runs.other)[col]
                return g
            extra_cols_generators = [f(c) for c in extra_cols]


        condition_vars = experimental_vars(study)
        writer = csv.writer(file)
        colnames = ['workerid', 'tasks_completed', 'censored', 
                    'start_time', 'end_time',
                    'local_start_time', 'local_end_time',
                    'country', 'local_time_zone_adjustment'] \
                    + ['condition_code'] + condition_vars + extra_cols
        writer.writerow(colnames)

        def clean(value):
            """
            returns a cleaned up value that can be used for csv export:
            - unicode text is encoded as such
            - None values are replaced with the given representation (default <NULL>)
            """
            if value == None:
                return null
            elif isinstance(value, unicode):
                return value.encode('utf8')
            elif isinstance(value,gluon.dal.Reference):
                return int(value)
            elif isinstance(value, timedelta):
                log('doing a timedelta %s' % value.seconds)
                return int(value.seconds)
            elif hasattr(value, 'isoformat'):
                return value.isoformat()[:19].replace('T', ' ')

            return value

        for record in runs:
            row = []
            for col in runs.colnames:
                if col == 'runs.other': continue
                if not table_field.match(col):
                    row.append(clean(record._extra[col]))
                else:
                    (t, f) = col.split('.')
                    if isinstance(record.get(t, None), (gluon.dal.Row,dict)):
                        row.append(clean(record[t][f]))
                    elif represent:
                        if runs.db[t][f].represent:
                            row.append(clean(runs.db[t][f].represent(record[f])))
                        else:
                            row.append(clean(record[f]))
                    else:
                        row.append(clean(record[f]))

            # Put localtime and other in there
            localtime = [clean(record.runs.start_time
                               + timedelta(hours=record.workers.time_zone)),
                         clean(record.runs.end_time
                               + timedelta(hours=record.workers.time_zone))]
            i = colnames.index('end_time') + 1
            row = row[:i] + localtime + row[i:]

            # Put the conditions in there
            vals = sj.loads(row.pop())           # Remove the json object
            for v in condition_vars:
                row.append(clean(vals[v]))

            other = [x(record) for x in extra_cols_generators]
            row = row + other
            
            writer.writerow(row)
        return runs

def captcha_csv(study):
    return claus_csv(study,
                     ['total time (hours)', 'completion rate (jobs/hour)', 'wage'],
                     [completion_time, completion_rate, wage])



# def claus_csv_old(study):
#     import re
#     table_field = re.compile('[\w_]+\.[\w_]+')
#     import csv
#     with open('study_%d.csv' % study.id, 'w') as f:
#         time_to_click = (db.runs.end_time - db.runs.start_time)/db.runs.length
        
#         runs = db((db.runs.study == study)
#                   & (db.workers.workerid == db.runs.workerid)
#                   & (db.countries.id == db.workers.country)
#                   & (db.conditions.id == db.runs.condition)) \
#                   .select(db.runs.workerid,
#                           db.runs.length,
#                           db.runs.start_time,
#                           db.runs.end_time,
#                           db.runs.censored,
#                           db.countries.name,
#                           db.workers.time_zone,
#                           time_to_click,
#                           db.runs.condition,
#                           db.conditions.json)

#         condition_vars = experimental_vars(study)
#         writer = csv.writer(f)
#         colnames = ['workerid', 'tasks_completed',
#                     'start_time', 'end_time',
#                     'local_start_time', 'local_end_time',
#                     'censored', 
#                     'country', 'local_time_zone_adjustment',
#                     time_to_click,
#                     'condition_code'] + condition_vars
#         writer.writerow(colnames)

#         def clean(value):
#             """
#             returns a cleaned up value that can be used for csv export:
#             - unicode text is encoded as such
#             - None values are replaced with the given representation (default <NULL>)
#             """
#             if value == None:
#                 return null
#             elif isinstance(value, unicode):
#                 return value.encode('utf8')
#             elif isinstance(value,gluon.dal.Reference):
#                 return int(value)
#             elif isinstance(value, timedelta):
#                 log('doing a timedelta %s' % value.seconds)
#                 return int(value.seconds)
#             elif hasattr(value, 'isoformat'):
#                 return value.isoformat()[:19].replace('T', ' ')

#             return value

#         for record in runs:
#             row = []
#             for col in runs.colnames:
#                 if not table_field.match(col):
#                     row.append(clean(record._extra[col]))
#                 else:
#                     (t, f) = col.split('.')
#                     if isinstance(record.get(t, None), (gluon.dal.Row,dict)):
#                         row.append(clean(record[t][f]))
#                     elif represent:
#                         if runs.db[t][f].represent:
#                             row.append(clean(runs.db[t][f].represent(record[f])))
#                         else:
#                             row.append(clean(record[f]))
#                     else:
#                         row.append(clean(record[f]))

#             # Put localtime in there
#             row.insert(4, clean(record.runs.start_time
#                                          + timedelta(hours=record.workers.time_zone)))
#             row.insert(5, clean(record.runs.end_time
#                                          + timedelta(hours=record.workers.time_zone)))

#             # Put the conditions in there
#             vals = sj.loads(row.pop())           # Remove the json object
#             for v in condition_vars:
#                 row.append(clean(vals[v]))

#             writer.writerow(row)
#         return runs


def price_func(row):
    return sj.loads(row.conditions.json)['price']
def width_func(row):
    return sj.loads(row.conditions.json)['width']

def r_test(study, x_func):
    runs = db((db.runs.study == study)
              & (db.runs.bad != True)
              & (db.workers.workerid == db.runs.workerid)
              & (db.countries.id == db.workers.country)
              & (db.conditions.id == db.runs.condition)) \
              .select(db.runs.workerid,
                      db.runs.length,
                      db.runs.censored,
                      db.runs.start_time,
                      db.runs.end_time,
                      db.countries.name,
                      db.workers.time_zone,
                      db.runs.condition,
                      db.conditions.json,
                      db.runs.other)

    #x = [(run.runs.length, x_func(run)) for run in runs]
    y = [run.runs.length for run in runs if sj.loads(run.conditions.json)['width'] == 30]
    n = len(y)
    x = range(n)
    x = [0,1]*(n/2 + 1)
    x = x[:n]
    x = [1] * n
    x[0] = 0
    if x_func:
        x = [x_func(row) for row in runs]
#     x = [1,2,4]
#     y = [2,4,6]


    r.assign('x', x)
    r.assign('y', y)
    r.par(ask=1, ann=0)
    r('hist(y, nclass=51)')
    return x

    assert(len(x) == len(y))
    fit = r.vglm(r('y ~ x'), r.tobit(Lower=1, Upper=51), trace=True)

    r.par(ask=1, ann=0)
    r.plot(x,y, main="Tobit model", las=1)
    print len(x), len(y)
    r.assign('y', y)
    r.lines(x, r.fitted(fit), col="red", lwd=2, lty="dashed")

    #fit = r('vglm(y ~ x, tobit(Lower=0, Upper=501), trace=TRUE)')
    return fit
              


