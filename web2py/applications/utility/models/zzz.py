'''

This utiliscope file is named zzz.py so that it will be run after all
other models/ files.

It loads hit information for live and testing hits.

'''

make_request_vars_convenient()
# Load the hit data
if request.live:
    # From live mturk hit
    # Url like: /captcha&live
    load_live_hit()
elif request.testing:
    # From the /test/captcha interface
    # Url like: /captcha&testing
    load_testing_hit()

make_request_vars_convenient()  # Run it again, updating request.price

# Send optional feedback in mail
if request.vars.feedback and len(request.vars.feedback) > 0:
    db.feedback.insert(workerid=request.workerid,
                       hitid=request.hitid,
                       assid=request.assid,
                       message=request.vars.feedback)
    db.commit()
    message = 'Message from:\nworker %s  for hit %s\nassignment %s\n\n"%s"' \
        % (request.workerid,
           request.hitid,
           request.assid,
           request.vars.feedback)
    #send_me_mail(message)
