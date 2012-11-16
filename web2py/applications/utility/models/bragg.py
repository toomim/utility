########### Jonathan Bragg's Studies
options.bragg = {
    # Put conditions / params stuff in here
    }


hit_params1 = {
         'title' : 'Finding questions in a problem set',
         'description' : 'You will draw a box around each problem in a problem set.',
         'keywords' : 'problem sets, segmentation, drawing, boxes',
         'assignments' : 1,
         'reward' : 0.08}
hit_params2 = {
         'title' : 'Finding the title of a course',
         'description' : 'Given a academic course-related document, find the descriptive title of the course and put that course in a category.',
         'keywords' : 'problem set, course, label, category',
         'assignments' : 1,
         'reward' : 0.04}
def schedule_j():
    task = 'pset/label3_1'
    name = 'label3 test1'
    description = 'testing 1'
    conditions = {'price':[0]}
    hit_params = hit_params2
    init_gen_study(task,name,description,conditions,hit_params)

def launch_j(taskName,low,high):
    launch_gen_hits(taskName,[{'id':i} for i in range(low,high)])


def init_gen_study(task, name, description, conditions, hit_params):
    # Yo JBragg, I basically made launch_study() do this so you can
    # probably use that instead now.
    #
    # But I didn't do anything to make it store options.task from
    # conditions like you do here, it still goes the other way, where
    # it derives this stuff FROM options.task.
    #
    # The idea is that you add options.bragg = {...} to the top of
    # this like at the top of captcha.py or keystroke.py.
    study = get_or_make_one(db.studies.name == name,
                            db.studies,
                            {'name' : name,
                             'launch_date' : datetime.now(),
                             'description' : description,
                             'task' : task,
                             'hit_params' : sj.dumps(hit_params, sort_keys=True)})
    study.update_record(conditions = sj.dumps(conditions, sort_keys=True))
    options.task = conditions
    db.commit()

# change so that individual hits can use different controllers?
def launch_gen_hits(study_name,arg_dict_list):
    study = get_one(db.studies.name == study_name)
    for arg_dict in arg_dict_list:
        schedule_hit(now, study.id, study.task, arg_dict)
