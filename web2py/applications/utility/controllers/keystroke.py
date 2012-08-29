######################

# coding: utf8
MAX_TYPOS = 1
MIN_STDEV = 6
KEYPHRASE = "The quick brown fox jumps over the lazy dog"
REQUIRED_RECORDINGS = 6
FAIL_CHANCE = 0.00

ENROLL_PRICE = 0.04

import random, hashlib, uuid, datetime, time, math
import gluon.contrib.simplejson

messages = dict(
    terse = dict(
        recordSuccess = "Example recorded.",
        recordAllDone = "Recorded all examples.",
        verifySuccess = "Verified.",
        verifyError = "Not recognized. Retry.",
        validateNotTyped = "Error. Retry.",
        validateTypos = "Bad typing sample. Retry.",
        validateStats = "Error. Retry."
    ),
    medium = dict(
        recordSuccess = "Typing pattern recorded.",
        recordAllDone = "Recorded all required examples.",
        verifySuccess = "Keystroke pattern verified.",
        verifyError = "Keystroke pattern not recognized. Try again.",
        validateNotTyped = "Error detecting keystrokes. Try again.",
        validateTypos = "Too many typos. Try again.",
        validateStats = "Error detecting keystrokes. Try again."
    ),
    verbose = dict(
        recordSuccess = "You successfully recorded your typing patterns.",
        recordAllDone = "You have recorded all of the needed examples of your typing patterns.",
        verifySuccess = "Your keystroke pattern was verified!",
        verifyError = "Sorry, your keystroke pattern was not recognized. Please try again.",
        validateNotTyped = "Sorry, there was a problem detecting your typing patterns. Please type the phrase normally.",
        validateTypos = "Sorry, there were too many typos. Please try to type the phrase more carefully.",
        validateStats = "Sorry, there was a problem detecting your typing patterns. Please type the phrase normally."
    ),
    authInstructions = "Type the following phrase normally.",
    recordInstructions = "keystroke", # Options: keystroke
    verifyInstructions = "keystroke", # Options: keystroke
)

def get_message(msgName):
    msg = messages[request.message_length][msgName]
    if request.yell:
        msg = msg.upper()
    return msg

if session.flashType:
    response.flashType = session.flashType
    session.flashType = None

response.title = "Authentication Research Study"

verificationAnswers = [
    "cow",
    "horse",
    "pig",
    "chicken",
    "lizard",
    "duck",
    "sheep",
    "dog",
    "cat",
    "fish",
    "penguin",
    "elephant",
    "giraffe"
]

verifications = [
    {"code":"fGRBdfmsoE", "answer":"chicken"},
    {"code":"pzXuFeat2D", "answer":"cat"},
    {"code":"jY03hZbM3G", "answer":"elephant"},
    {"code":"Sx9oL4sXMJ", "answer":"sheep"},
    {"code":"lXvWqk1b1o", "answer":"cow"},
    {"code":"IhX17rARJ9", "answer":"chicken"},
    {"code":"Z4tlHSvndP", "answer":"lizard"},
    {"code":"rC5vPxC1JV", "answer":"horse"},
    {"code":"DCwGF1DPYR", "answer":"dog"},
    {"code":"RlpOflCqUS", "answer":"horse"},
    {"code":"6qN7XLChXd", "answer":"penguin"},
    {"code":"1PJjDX5NUp", "answer":"pig"},
    {"code":"ybogV7ohqG", "answer":"dog"},
    {"code":"noZzU4M7uT", "answer":"cow"},
    {"code":"FLGFG9OEGf", "answer":"lizard"},
    {"code":"mx4qXwPtaJ", "answer":"giraffe"},
    {"code":"fBuQfGgxxh", "answer":"fish"},
    {"code":"0iBVgqT2oN", "answer":"horse"},
    {"code":"fp8WRPMCWJ", "answer":"elephant"},
    {"code":"hgendcJot7", "answer":"horse"},
    {"code":"t3xJEqangh", "answer":"giraffe"},
    {"code":"aR0SWYyl4H", "answer":"dog"},
    {"code":"lqyCGoW7nX", "answer":"cat"},
    {"code":"37zVw4yY8G", "answer":"sheep"},
    {"code":"MEzPbkeQII", "answer":"giraffe"},
    {"code":"YNO37YE9zP", "answer":"penguin"},
    {"code":"xJRF9wBviB", "answer":"duck"},
    {"code":"9T66hl3ruv", "answer":"penguin"},
    {"code":"iCHgq2CLSs", "answer":"sheep"},
    {"code":"D35tgq0FLn", "answer":"cat"},
    {"code":"sCxwDCQuHn", "answer":"elephant"},
    {"code":"ILNGtlB4FN", "answer":"fish"},
    {"code":"PxtPh7iK9v", "answer":"lizard"},
    {"code":"b9ypnd0Txb", "answer":"duck"},
    {"code":"VtFRAICFGF", "answer":"lizard"},
    {"code":"g3fSmKn6yY", "answer":"sheep"},
    {"code":"yRneW8CTqY", "answer":"cat"},
    {"code":"YrQFB2oVHW", "answer":"fish"},
    {"code":"wHSEGWMwAt", "answer":"pig"},
    {"code":"pnzXySwQKK", "answer":"elephant"},
    {"code":"aMhaFAhlXu", "answer":"pig"},
    {"code":"Pfrzr0jrTo", "answer":"duck"},
    {"code":"DbVzqBni7i", "answer":"dog"},
    {"code":"VXCPHcXvp7", "answer":"penguin"},
    {"code":"DCCuIUaED2", "answer":"chicken"},
    {"code":"IUacrJDHTs", "answer":"cow"},
    {"code":"7Phtq9fBNW", "answer":"giraffe"},
    {"code":"WBgX6RCem7", "answer":"chicken"},
    {"code":"spUVHcVJBh", "answer":"cow"},
    {"code":"RrQsTKsrq8", "answer":"duck"},
    {"code":"xufN9TJeMi", "answer":"pig"},
    {"code":"IardZqBAGk", "answer":"fish"}
]

hit_session = None

def index():

    if request.preview:
        return dict(messages=messages)
        
    '''Shows the welcome information, study description, etc.'''
    block_multiple(False)
    
    if hit_session and hit_session.phase != 'index':
        redirect(URL(f=hit_session.phase, vars=request.get_vars))
    
    #If the user has already completed a hit, they skip this part
    if (hits_done(request.workerid, request.study) >= 1 or (not request.live and request.vars.hits_completed >= 1)):
        #If testing, use the hits_completed parameter
        if hit_session:
            hit_session.phase = 'verify'
            hit_session.attempts = 0
        redirect(URL(f='verify', vars=request.get_vars))
    
    # we start off in the record phase
    if hit_session:
        hit_session.phase = 'record'
    
    response.isEnrollment = True
    request.enrollPrice = ENROLL_PRICE
    request.verifyPrice = request.price;
    
    return dict(messages=messages)
    
##
## The following actions are used during the enrollment HIT
##

def record():
    '''Shows the record form and processes recordings'''
    
    #No visiting this page during preview
    if request.preview:
        record_action('routing: record() during preview')
        redirect(URL(f='index', vars=request.get_vars))
    
    block_multiple(True)
    
    #Initialize successfulRecordings to 0 if not set yet
    if not hit_session.successfulRecordings:
        hit_session.successfulRecordings = 0

    #If they're already enrolled go on to the enrolled action
    if hit_session.phase != 'record':
        record_action('routing: record() when in ' + hit_session.phase)
        redirect(URL(f=hit_session.phase, vars=request.get_vars))
    
    form = auth_form(messages['authInstructions'], KEYPHRASE)
    
    #validate the recording
    if form.process(onsuccess=None, onfailure=None).accepted and validate(request.vars.typing, request.vars.text, form):
        record_action('user recorded', request.vars.typing)
        response.flash = get_message('recordSuccess')
        response.flashType = "success"
        hit_session.successfulRecordings += 1
    elif form.errors:
        record_action('invalid: record', form.errors)
        
    #They've submitted all required recordings
    if hit_session.successfulRecordings >= REQUIRED_RECORDINGS:
        record_action('recordings completed')
        hit_session.phase = 'enrolled'
        hit_session.invalid_verifs = 0
        session.flash = get_message('recordAllDone')
        session.flashType = "success"
        redirect(URL(f='enrolled', vars=request.get_vars))

    response.isEnrollment = True
    request.enrollPrice = ENROLL_PRICE
    request.verifyPrice = request.price;
    
    if hit_session.successfulRecordings > 0:
        request.scrollDown = True
        
    result = dict()
    result['keyphrase'] = KEYPHRASE
    result['requiredRecordings'] = REQUIRED_RECORDINGS
    result['successfulRecordings'] = hit_session.successfulRecordings
    result['form'] = form
    result['messages'] = messages
    return result

def enrolled():
    '''
    All required sessions were recorded.
    Shows a brief enrollment questionnaire.
    '''
    
    #No visiting this page during preview
    if request.preview:
        record_action('routing: enrolled() during preview')
        redirect(URL(f='index', vars=request.get_vars))
    
    block_multiple(True)
    
    hit_session.successfulRecordings = 0
    
    #If they're not enrolled, go back to record
    if hit_session.phase != 'enrolled':
        record_action('routing: enrolled() when in ' + hit_session.phase)
        redirect(URL(f=hit_session.phase, vars=request.get_vars))
    
    ageItem = form_item("What is your age, in years? (required)", 
        INPUT(_type="text",_name="age",_autocomplete="off", requires=[
            IS_NOT_EMPTY(error_message="Age is required"), 
            IS_INT_IN_RANGE(0, 200,error_message="Enter your age in years"),
            IS_INT_IN_RANGE(18, 200, error_message="You must be 18 or older to participate")]))
    
    occupationItem = form_item("What is your occupation? (required)", 
        INPUT(_type="text",_name="occupation",_autocomplete="off",
        requires=IS_NOT_EMPTY(error_message="Occupation is required")))
    
    genderInputs = [
        LABEL(INPUT(_type="radio", _name="gender", _value='female', _id="gender-female", requires=IS_NOT_EMPTY(error_message="Gender is required")),
            'Female',
            _for="gender-female", _class="radio"),
        LABEL(INPUT(_type="radio", _name="gender", _value='male', _id="gender-male"),
            'Male',
            _for="gender-male", _class="radio")
    ]
    genderItem = form_item("What is your gender? (required)", genderInputs)
  
    incomeInputs = [
        LABEL(INPUT(_type="radio", _name="income", _value='0', _id="income-0", requires=IS_NOT_EMPTY(error_message="Income is required")),
            'Less than $10,000',
            _for="income-0", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='1', _id="income-1"),
            '$10,000 to $19,999',
            _for="income-1", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='2', _id="income-2"),
            '$20,000 to $29,999',
            _for="income-2", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='3', _id="income-3"),
            '$30,000 to $39,999',
            _for="income-3", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='4', _id="income-4"),
            '$40,000 to $49,999',
            _for="income-4", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='5', _id="income-5"),
            '$50,000 to $59,999',
            _for="income-5", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='6', _id="income-6"),
            '$60,000 to $69,999',
            _for="income-6", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='7', _id="income-7"),
            '$70,000 to $79,999',
            _for="income-7", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='8', _id="income-8"),
            '$80,000 to $89,999',
            _for="income-8", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='9', _id="income-9"),
            '$90,000 to $99,999',
            _for="income-9", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='10', _id="income-10"),
            '$100,000 to $149,999',
            _for="income-10", _class="radio"),
        LABEL(INPUT(_type="radio", _name="income", _value='11', _id="income-11"),
            '$150,000 or more',
            _for="income-11", _class="radio"),
    ]
    incomeItem = form_item("What is your total annual household income in US dollars? (required)", incomeInputs)
    
    biometricInputs = [
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='fingerprint', _id="biometric-fingerprint", requires=IS_NOT_EMPTY(error_message="You must answer the question about identification systems.")),
            'Fingerprints',
            _for="biometric-fingerprint", _class="checkbox"),
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='eye', _id="biometric-eye"),
            'Iris or retina scans',
            _for="biometric-eye", _class="checkbox"),
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='face', _id="biometric-face"),
            'Face recognition',
            _for="biometric-face", _class="checkbox"),
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='voice', _id="biometric-voice"),
            'Voice recognition',
            _for="biometric-voice", _class="checkbox"),
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='signature', _id="biometric-signature"),
            'Signature recognition',
            _for="biometric-signature", _class="checkbox"),
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='keystroke', _id="biometric-keystroke"),
            'Keystroke (typing) pattern',
            _for="biometric-keystroke", _class="checkbox"),
    ]
    biometricInputs = randomize('biometric', biometricInputs);
    biometricInputs.append(
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='other', _id="biometric-other"),
            'Other biometric systems',
            _for="biometric-other", _class="checkbox"))
    biometricInputs.append(
        LABEL(INPUT(_type="checkbox", _name="biometric", _value='none', _id="biometric-none"),
            'I have never used any of these',
            _for="biometric-none", _class="checkbox"))
    
    set_exclusion('biometric', 'biometric-none')
    
    biometricItem = form_item("Which of the following identification systems have you used before? (required)", biometricInputs)
    
    verificationItem = verify_item('verify')
    
    submitButton = submit_button('submit')
    form = FORM(ageItem, genderItem, occupationItem, incomeItem, biometricItem, verificationItem, submitButton, _id="enrolled-form", _class="questions well")
    
    if form.process(onfailure="").accepted:
        
        # save the form answers
        record_entry_survey(request.post_vars)
        
        # complete the HIT
        del session[session.current_hit]
        session.current_hit = None
        # set the price to the enrollment price
        alter_price(ENROLL_PRICE)
        hit_finished()
        
        session.flash = "The HIT has been submitted."
        session.flashType = "success"
        redirect(URL(f='thanks', vars=request.get_vars))
    elif form.errors:
        if 'verify' in form.errors:
            hit_session.invalid_verifs += 1
        record_action('invalid: enrolled', form.errors)
        
    response.isEnrollment = True
    request.enrollPrice = ENROLL_PRICE
    request.verifyPrice = request.price;
    
    return dict(form=form, messages=messages)

##
## The following actions are used during the authentication HITs
##

def verify(): 

    #No visiting this page during preview
    if request.preview:
        record_action('routing: verify() during preview')
        redirect(URL(f='index', vars=request.get_vars))

    block_multiple(False)

    if hit_session and hit_session.phase != 'verify':
        record_action('routing: verify() when in ' + hit_session.phase)
        redirect(URL(f=hit_session.phase, vars=request.get_vars))

    form = auth_form(messages['authInstructions'], KEYPHRASE)
    
    if hit_session and form.process(onsuccess=None, onfailure=None).accepted and validate(request.vars.typing, request.vars.text, form):
        #validate the recording
        if authorize("XYZ"):
            #if they were authenticated, go on to questionnaire
            record_action('user authorized', request.vars.typing)
            hit_session.phase = 'verified'
            hit_session.invalid_verifs = 0
            session.flash = get_message('verifySuccess')
            session.flashType = "success"
            redirect(URL(f='verified', vars=request.get_vars))
        else:
            record_action('user denied', request.vars.typing)
            form.errors = dict(text=get_message('verifyError'))
    elif form.errors:
        record_action('invalid: verify', form.errors)

    if hit_session:
        hit_session.attempts += 1
        
    return dict(keyphrase=KEYPHRASE, form=form, messages=messages)

def verified():
    #No visiting this page during preview
    if request.preview:
        record_action('routing: verified() during preview')
        redirect(URL(f='index', vars=request.get_vars))

    block_multiple(True)
        
    if hit_session.phase != 'verified':
        record_action('routing: verified() when in ' + hit_session.phase)
        redirect(URL(f=hit_session.phase, vars=request.get_vars))
    
    frustrationInputs = [
        LABEL(INPUT(_type="radio", _name="frustration", _value='1', _id="frustration-0", requires=IS_NOT_EMPTY(error_message='You must rate your frustration')),
            'Not at all frustrating',
            _for="frustration-0", _class="radio"),
        LABEL(INPUT(_type="radio", _name="frustration", _value='2', _id="frustration-1"),
            'Slightly frustrating', 
            _for="frustration-1", _class="radio"),
        LABEL(INPUT(_type="radio", _name="frustration", _value='3', _id="frustration-2"),
            'Moderately frustrating', 
            _for="frustration-2", _class="radio"),
        LABEL(INPUT(_type="radio", _name="frustration", _value='4', _id="frustration-3"),
            'Very frustrating', 
            _for="frustration-3", _class="radio"),
        LABEL(INPUT(_type="radio", _name="frustration", _value='5', _id="frustration-4"),
            'Extremely frustrating', 
            _for="frustration-4", _class="radio")
    ]
    frustrationItem = form_item("How frustrating was typing the phrase to verify your identity? (required)", frustrationInputs)
    
    verificationItem = verify_item('verify')
    
    submitButton = submit_button('submit')
    form = FORM(frustrationItem, verificationItem, submitButton, _id="verified-form", _class="questions well")
    
    if form.process(onfailure="").accepted:
        # save the questionnaire
        record_post_survey(request.post_vars)
        
        # complete the HIT
        del session[session.current_hit]
        session.current_hit = None
        hit_finished()
        
        session.flash = "The HIT has been submitted."
        session.flashType = "success"
        redirect(URL(f='thanks', vars=request.get_vars))
    elif form.errors:
        if 'verify' in form.errors:
            hit_session.invalid_verifs += 1
        record_action('invalid: verified', form.errors)
        
    return dict(form=form, messages=messages)

def thanks():
    '''Display a thank you message'''
    
    #No visiting this page during preview
    if request.preview:
        record_action('routing: thanks() during preview')
        redirect(URL(f='index', vars=request.get_vars))
    
    return dict(messages=messages)
    
##
## These are private functions
##

def initialize_hit(hitid):
    log_action('initialized hit')
    session.current_hit = hitid
    session[hitid] = gluon.storage.Storage()
    session[hitid].phase = 'index'
    session.start_time = time.time()

def block_multiple(redirectToIndex):
    global hit_session
    
    hit = request.hitid
    if session.current_hit and session.current_hit != hit:
        # they are starting a new hit
        if request.vars.unblock:
            # they've said they don't care, they want to do this one anyway
            record_action('unblocked')
            initialize_hit(hit)
            hit_session = session[hit]

            rvars = request.get_vars
            del rvars['unblock']
            redirect(URL(f='index', vars=rvars))
        else:
            # we need to either go back to index to show the dialog
            # or if we aren't going back, show it now
            if redirectToIndex:
                redirect(URL(f='index', vars=request.get_vars))
            else:
                record_action('blocked')
                response.block = True
    else:
        #if we're starting or resuming a hit
        if session.current_hit != hit:
            initialize_hit(hit)
            if (hits_done(request.workerid, request.study) >= 1) or (not request.live and request.vars.hits_completed >= 1):
                session[hit].phase = 'verify'
                session[hit].attempts = 0
        session.current_hit = hit
        hit_session = session[session.current_hit]

def submit_button(name):
    return DIV(
        INPUT(_type="submit",_name=name, _value="Submit HIT", _class="btn btn-primary btn-large"),
        SPAN("You may complete as many additional HITs in this group as you want.", _class="reminder-text")
    )

def uniquify(seq):
    # Dave Kirby
    # Order preserving uniquify
    # http://www.peterbe.com/plog/uniqifiers-benchmark (f8)
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def set_exclusion(groupName, excluderId):
    '''Sets up an exclusive relationship within a set of checkboxes. Useful for item1, item2, item3, none questions'''
    if not response.exclusions:
        response.exclusions = []
    response.exclusions.append((groupName, excluderId))

def randomize(name, questions):
    keys = None
    if session.randoms and session.randoms[name]:
        #retrieve an old order
        keys = session.randoms[name]
        
        #make sure it is consistent
        if len(keys) != len(questions):
            keys = None
    
    if not keys:
        #generate a new order
        keys = range(0, len(questions))
        random.shuffle(keys)
    
    #store the random order
    if not session.randoms:
        session.randoms = {}
    session.randoms[name] = keys
    
    orderedQuestions = []
    for index in keys:
        orderedQuestions.append(questions[index])
    
    return orderedQuestions
    
def verify_item(name):
    
    verificationIndex = hits_done(request.workerid, request.study)
    
    if not request.live and ("hits_completed" in request.vars):
        verificationIndex = int(request.vars.hits_completed)
        
    item = verifications[verificationIndex]
    answer = item["answer"]
    imgSrc = URL("static", "keystroke/verify/" + item["code"] + ".jpg")
    
    answerList = [answer]
    while len(answerList) < 5:
        verificationIndex += 7
        item = verifications[verificationIndex % len(verifications)]
        if item["answer"] not in answerList:
            answerList.append(item["answer"])
    
    random.shuffle(answerList)
    
    validators = [
        IS_NOT_EMPTY(error_message='You must identify the animal in the image'),
        IS_EQUAL_TO(answer, error_message='You did not select the correct animal!')
    ]
    
    verificationInputs = []
    
    for idx, answer in enumerate(answerList):
        animalId="ver-" + answer
        verificationInputs.append(
            LABEL(INPUT(_type="radio", _name=name, _value=answer, _id=animalId, requires=validators),
                answer, 
                _for=animalId, _class="radio")
            )
    
    verifyPic = IMG(_src=imgSrc)
    loading = DIV(verifyPic, _class="img-loading")
    
    verificationItem = form_item("Which animal is shown in the following image? (required)", verificationInputs, loading)
    return verificationItem

def form_item(prompt, inputs, *args):
    answers = DIV(_class="answers")
    
    if not isinstance(inputs, (list, tuple)):
        inputs = [inputs]
        
    for idx, input in enumerate(inputs):
        answers.append(input)

    question = DIV(_class="question")
    question.append(prompt)
    
    item = DIV(_class="item")
    item.append(question)
    item.append(answers)
    
    for arg in args:
        item.append(arg)
    
    return item

def auth_form(instructions, keyphrase):
    return FORM(
        DIV(instructions, _class="auth-instructions"),
        
        INPUT(_name="keyphrase", _type="hidden", _value=keyphrase),
        INPUT(_name="typing", _type="hidden", _id="typing-input"),
        
        DIV(keyphrase, _id="auth-example"),
        INPUT(_name="text", _type="text", _id="auth-field", _autocomplete="off", _value=""),
        
        INPUT(_name="submitbutton", _type="submit", _id="auth-submit", _class="btn btn-primary", _value="Submit"),
        DIV("analyzing typing patterns...", _class="loading", _style="display: none"),
        
        _id="auth-form", _method="post", _class="well form-inline")
    
def validate(typing, text, form):
    if not typing or not text:
        form.errors['text'] = get_message('validateNotTyped')
        return False

    typing = gluon.contrib.simplejson.loads(typing)
    keyphrase = KEYPHRASE

    # check for typos that the string matches
    typos = LD(keyphrase, text)
    
    # get statistics about the seeks and presses
    seeks, presses = distributions(typing)

    valid = True

    if len(text) * 2 > len(typing):
        form.errors['text'] = get_message('validateNotTyped')
        record_action('insufficient keypresses', len(typing))
        valid = False
    elif typos > MAX_TYPOS:
        form.errors['text'] = get_message('validateTypos')
        record_action('too many typos', typos)
        valid = False
    else:
        seek_stats = statistics(seeks)
        press_stats = statistics(presses)

        if not validStats(seek_stats):
            form.errors['text'] = get_message('validateStats')
            record_action('invalid seek_stats', seek_stats)
            valid = False
        elif not validStats(press_stats):
            form.errors['text'] = get_message('validateStats')
            record_action('invalid press_stats', press_stats)
            valid = False

    return valid

def prepareData(seeks, presses):
    data = {}
    bin_size = 2

    max_time = max(max(seeks), max(presses)) + bin_size
    max_time = max_time - (max_time % bin_size) # make it end on a bin
    for time in range(0, max_time, bin_size):
        data[time] = [str(time), 0, 0]

    for seek in seeks:
        time = seek - seek % bin_size
        data[time][1] += 1
    for press in presses:
        time = press - press % bin_size
        data[time][2] += 1

    values = []
    for key in sorted(data.iterkeys()):
        values.append(data[key])
    return values

def authorize(user_id):
    sleep_time = request.delay_time;
    time.sleep(sleep_time)
    if random.random() > request.reject_chance:
        return True
    else:
        return False

def validStats(stats):
    threshold = MIN_STDEV
    return stats["stdev"] > threshold

def LD(s,t):
    s = ' ' + s.lower()
    t = ' ' + t.lower()
    d = {}
    S = len(s)
    T = len(t)
    for i in range(S):
        d[i, 0] = i
    for j in range (T):
        d[0, j] = j
    for j in range(1,T):
        for i in range(1,S):
            if s[i] == t[j]:
                d[i, j] = d[i-1, j-1]
            else:
                d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + 1)
    return d[S-1, T-1]

def distributions(typing):
    seekTimes = []
    pressTimes = []

    lastTime = 0
    for i, event in enumerate(typing):
        type = event["type"]
        time = event["time"]
        if type == "down":
            seekTimes.append(time - lastTime)
            lastTime = time
        elif type == "up":
            pressTimes.append(time - lastTime)
            lastTime = time
    return seekTimes, pressTimes

def statistics(values):

    mean = sum(values) / max(len(values), 1)
    variance = sum([(value - mean)**2 for value in values]) / max(len(values) - 1, 1)
    stdev = math.sqrt(variance)

    return dict(mean=mean, variance=variance, stdev=stdev)

def frequencies(values):
    freq = {}
    for v in values:
        if v not in freq:
            freq[v] = 0
        freq[v] = freq[v] + 1
    return freq


