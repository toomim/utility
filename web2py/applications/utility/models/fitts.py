# #######################
def fitts_id(iframe_width, rectangle_width):
    # The distance is from the middle of each rectangle, which
    # subtracts from iframe half the rectangle twice
    distance = iframe_width - rectangle_width
    distance = 900
    ratio = float(rectangle_width) / float(distance)
    log(ratio)
    import math
    return math.log(ratio + 1, 2)

def study_fitts_times(study):
    result = {}
    for c in available_conditions(study):
        result[c.id] = study_cond_fitts_times(study, c)
    return result

def study_cond_fitts_times(study, condition):
    return fitts_times((db.actions.study == study)
                       & (db.actions.condition == condition))
def fitts_times(query):
    ''' Takes a query over the actions table '''
    rows = db(query & (actions.action == 'fitts results')).select()
    time_sum = sum([sum([clicks['click_time'] for clicks in sj.loads(row.other)['clicks'][1:]])
                    for row in rows])

    count_sum = sum([max([clicks['count'] for clicks in sj.loads(row.other)['clicks'][1:]])
                    for row in rows])

    return float(time_sum)/count_sum

def fitts_times_by_var(study, var, times=None):
    times = times or study_fitts_times(study)
    result = {}
    cs_by_var = study_conditions_by_var(study, var)
    for val, cs in cs_by_var.items():
        result[val] = sum([times[c.id] for c in cs]) / float(len(cs))
    return result

def fitts_times_old(study):
    result = []
    for c in available_conditions(study):
        rows = db((db.actions.study == study)
                  & (db.actions.condition == c)
                  & (db.actions.action == 'fitts results')).select()
        sum = 0
        count = 0
        log('Num rows for %s is %s' % (c.id,str(len(rows))))
        for row in rows:
            if not row.other:
#                 log(row.other)
                continue
            data = sj.loads(row.other)
#             if not 'click_time' in data:
#                 log('bad data ' + data)
            if 'click_time' in data: # and data['click_time'] < 
                sum += data['click_time']
                count += 1
        time = float(sum)/count if count != 0 else -1
        result.append(Storage(dict(condition=c.id,
                                   time=time,
                                   count=count)))
    return result

def annotate_fitts_runs(study):
    for run in db(db.runs.study==study).select():
        run.update_record( \
            other = sj.dumps( \
                {'click_time' : \
                     fitts_times((actions.workerid == run.workerid)
                                 & (actions.time >= run.start_time)
                                 & (actions.time <= run.end_time))}))
    db.commit()


def fitts_csv(study):
    time_per_condition = study_fitts_times(study)
    def to_hourly(dollars_per_ms):
        return '%.2f' % (dollars_per_ms * 1000 * 60 * 60)
    def click_time(row):
        return '%d' % sj.loads(row.runs.other)['click_time']
    def task_wage(row):
        price = sj.loads(row.conditions.json)['price']
        width = sj.loads(row.conditions.json)['width']
        width_time = fitts_times_by_var(study,
                                        'width',
                                        time_per_condition)[width]
        num_tasks = sj.loads(row.conditions.json)['num_tasks']
        log('Dealing with price=%s, width=%s, width_time=%s, num_tasks=%s' %
                      (price, width, width_time, num_tasks))
        return to_hourly(price / (width_time * num_tasks))

    def personal_wage(row):
        price = sj.loads(row.conditions.json)['price']
        time = sj.loads(row.runs.other)['click_time']
        num_tasks = sj.loads(row.conditions.json)['num_tasks']
        return to_hourly(price / (time * num_tasks))


    return claus_csv(study,
                     ['click time (ms)', 'wage (mean for task)', 'personal wage'],
                     [click_time, task_wage, personal_wage])

