import os

def prompt():
    """
    Set to the prompt you want using fkpromptid
    prompts the user for a responses or saves it to the db
    if it has just returned from the prompt
    url parameters:
    prompt: question to ask the user to write about
    example: example of a decent submission
    assignmentId: from mechanical turk
    Second time:
    if request.vars.response, then it inserts the response and does
    hit_finished()
    """
    #request.vars.workerId = 2
    #This will need to pass on the assignmentid to the view
    #Also, it must be given assignmentId
    log('in prompt: ' + str(request.vars))
    log('SELECT id, prompt FROM prompt p ' + 
    'WHERE NOT EXISTS(SELECT * FROM response ra WHERE ra.fkpromptid == p.id AND ra.workerId == \'' + request.vars.workerId + '\' )')
    prompt2 = 'ERROR: no prompt'
    example2 = 'ERROR: no example'
    found = False
    for row in db.executesql('SELECT id, prompt FROM prompt p ' + 
    'WHERE NOT EXISTS(SELECT * FROM response ra WHERE ra.fkpromptid == p.id AND ra.workerid == \'' + request.vars.workerId + '\' )'):
        log('1')
        prompt2=row[1]
        log('2')
        request.vars.fkpromptid = row[0]
        log('3')
        found = True
    if not found:
        redirect(URL(r=request,f='notasks'))
    
    #Has it already gotten a response to the prompt?
    if request.vars.response:
        log('request.vars.response set')
        log(request.vars)
        #yes, save to db and redirect to mechanical turk
        db.response.insert(fkpromptid=request.vars.fkpromptid,response=request.vars.response,assignmentid=request.vars.assignmentId,labelings=0,time=now,
        workerid=request.vars.workerId)
        log('%s %s' % (request.vars.testing, request.testing))
        request.vars.testing=request.testing
        hit_finished()
    
    request.vars.prompt=prompt2
    return dict(prompt=prompt2)
    
    #No rows found, redirect to notasks.html
    redirect(URL(r=request,f='notasks'))


# def my_crazy_hit():
#     return {'Hello' : "there"}

    
def notasks():
    """
    Displayed when the user cannot perform additional hits
    """
    return dict()
