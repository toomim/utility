
options.keystroke = {
    'price' : [0.01, 0.02],
    'reject_chance': [0.00, 0.05, 0.10, 0.33, 0.66, 1],
    'delay_time': [0.1, 2, 5],
    'message_length': ['terse', 'medium', 'verbose'],
    'yell' : [True, False],
    'work_limit' : 51,
    'mystery_task' : True
    }


db.define_table('ks_entry_surveys',
                db.Field('study', db.studies),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('assid', 'text'),
                db.Field('time', 'datetime', default=now),
                db.Field('ip', 'text'),
                db.Field('condition', db.conditions),
                db.Field('age', 'integer'),
                db.Field('gender', 'text'),
                db.Field('occupation', 'text'),
                db.Field('biometric', 'text'),
                db.Field('verification', 'text'),
                db.Field('duration', 'integer'),
                migrate=migratep, fake_migrate=fake_migratep)

db.define_table('ks_post_surveys',
                db.Field('study', db.studies),
                db.Field('hitid', 'text'),
                db.Field('workerid', 'text'),
                db.Field('assid', 'text'),
                db.Field('time', 'datetime', default=now),
                db.Field('ip', 'text'),
                db.Field('condition', db.conditions),
                db.Field('completed', 'integer'),
                db.Field('attempts', 'integer'),
                db.Field('duration', 'integer'),
                db.Field('frustration', 'integer'),
                db.Field('verification', 'text'),
                db.Field('invalid_verifs', 'integer'),
                migrate=migratep, fake_migrate=fake_migratep)

def record_entry_survey(post):
    hit = request.hitid
    worker = request.workerid
    ass = request.assid
    ip = request.env.remote_addr
    condition = get_condition(request.condition)
    duration = time.time() - session.start_time
    
    age = post.age
    gender = post.gender
    occupation = post.occupation
    biometric = sj.dumps(post.biometric)
    verification = post.verify
    
    db.ks_entry_surveys.insert(study=request.study,
                      hitid=hit,
                      workerid=worker,
                      assid=ass,
                      ip=ip,
                      condition=condition,
                      age=age,
                      gender=gender,
                      occupation=occupation,
                      biometric=biometric,
                      verification=verification,
                      duration=duration)
                      
def record_post_survey(post):
    hit = request.hitid
    worker = request.workerid
    ass = request.assid
    ip = request.env.remote_addr
    condition = get_condition(request.condition)
    duration = time.time() - session.start_time
    
    attempts = hit_session.attempts
    completed = hits_done(request.workerid, request.study)
    frustration = post.frustration
    verification = post.verify
    invalid_verifs = hit_session.invalid_verifs
    
    db.ks_post_surveys.insert(study=request.study,
                      hitid=hit,
                      workerid=worker,
                      assid=ass,
                      ip=ip,
                      condition=condition,
                      completed=completed,
                      attempts=attempts,
                      frustration=frustration,
                      verification=verification,
                      invalid_verifs=invalid_verifs,
                      duration=duration)
