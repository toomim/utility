
def schedule_ipcaptchas(num_hits, name, description):
    controller_func = 'hits/show_captcha'
    conditions = {
        'price' : [.01, .02],
        'style' : ['pretty', 'ugly'],
        'captchas_per_task' : [10]
        }
    study = get_or_make_one(db.studies.name == name,
                            db.studies,
                            {'name' : name,
                             'launch_date' : now,
                             'description' : description,
                             'conditions' : sj.dumps(conditions),
                             'controller_func' : controller_func})
    for i in range(num_hits):
        schedule_hit(now, study.id, controller_func, {})

def schedule_fitts(num_hits, name, description):
    task = 'fitts'
    conditions = {
        'price' : [.00, .06, .01],
        'style' : ['classic fitts'], #'scattered'],
        'width' : [300],
        'num_tasks' : [40]
        }
    schedule_study(num_hits, task, conditions, name, description)

# def schedule_fitts_bounds(num_hits, name, description):
#     task = 'fitts'
#     conditions = {
#         'price' : [.01, .03],
#         'style' : ['classic fitts'], #'scattered'],
#         'width' : [3,  30, 300],
#         'num_tasks' : [100]
#         }
#     schedule_study(num_hits, task, conditions, name, description)

def schedule_chi2010_captchas(num_hits, name, description):
    task = 'show_captcha'
    conditions = {
        'price' : [.01, .02],
        'style' : ['pretty', 'ugly'],
        'num_tasks' : [10]
        }
    schedule_study(num_hits, task, conditions, name, description)
