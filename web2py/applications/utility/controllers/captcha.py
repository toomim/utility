#####################################################################################
################
################  Captcha 1
################
#####################################################################################




import applications.utility.modules.captcha as captcha

def count_down_guts(query, insert_f):
   rows=db(query).select()
   if len(rows) == 0:
       insert_f()
       rows=db(query).select()

   if rows[0].waiting:
       return 'blocked'
   
   rows[0].update_record(waiting = True)
   count = rows[0].count
   rows[0].update_record(waiting = False)

   if count != 0:
       count -= 1
       rows[0].update_record(count=count)

   return count

def count_down(counting_from):
    def ins(): db.countdown.insert(count=counting_from, assid = request.assid)
    return count_down_guts((db.countdown.assid==request.assid),
                           ins)

captcha_public_key = '6Lf8zwcAAAAAAG7tPpNsTcIPiyLM-5J9Y0kMdIJj'
captcha_private_key = '6Lf8zwcAAAAAAJvaV0u2J2k-M43PL4MkFeqJuEV6'
def show_captcha():
    if (request.total_count or request.num_tasks) and not request.captchas_per_task:
        request.captchas_per_task = (request.total_count or request.num_tasks)

#     # Default values
#     if request.testing:
#         if not request.price: request.price = 0.01
#         if not request.captchas_per_task: request.captchas_per_task = 2

    pay_string = '$%.2f' % request.price

    # Check the answer we just got if there is one
    if request.vars.recaptcha_response_field:
        test = captcha.submit(request.vars.recaptcha_challenge_field,
                              request.vars.recaptcha_response_field,
                              captcha_private_key,
                              request.env.remote_addr)
        if test.is_valid:
            record_action('good guess')
            count = count_down(request.captchas_per_task)
            log('Good guess #%s' % (request.captchas_per_task-count))
            if count == 0:
                response.midflash = 'Done!'
                log('Someone finished this captcha!  let\'s give them ' + str(request.price))
                hit_finished()
            elif count != 'blocked':
#                response.midflash = XML('Correct, just ' + str(count) + ' more<br>until you earn ' + pay_string)
                response.midflash = 'Correct, just ' + str(count) + ' captchas left'
            else:
                record_action('blocked')
        else:
            response.midflash = "bad. try again."
            log('They took a bad guess')
            record_action('bad guess')
    else:
        from gluon import current
        current.is_preview()
        record_action('preview' if is_preview() else 'display')
        log(('Preview! with hitid=%s'%request.hitid) if is_preview() else 'display!')

    if is_preview():
        submitter = INPUT(_type='submit', _value='Submit', _disabled="true")
    else:
        submitter = INPUT(_type='submit')

    final_word = '<p style="padding-top: 28px;">This is a research study.  We are not spammers.  <br/>The prices and tasks change over time, so try again later if you do not like this task or price.</p>'

    feedback_box = XML('<p>Optional hit feedback: <input type="text" name="feedback"' \
                       + ('disabled=True' if is_preview() else '') \
                       + '/></p>')

    return dict(form=FORM(XML(captcha.displayhtml(captcha_public_key, disabled=is_preview())),
                          submitter,
                          XML(final_word),
                          feedback_box),
                total=request.captchas_per_task,
                pay=pay_string)



def index():
    checkpoint('Starting captcha')
    # Check the answer we just got if there is one
    if request.vars.recaptcha_response_field:
        test = captcha.submit(request.vars.recaptcha_challenge_field,
                              request.vars.recaptcha_response_field,
                              captcha_private_key,
                              request.env.remote_addr)
        if test.is_valid:
            record_action('good guess')
            count = count_down(request.num_tasks)
            debug('Good guess #%s', (request.num_tasks - count))
            if count == 0:
                response.midflash = 'Done!'
                debug('Someone finished this captcha!  let\'s give them %s',
                      request.price_string)
                hit_finished()
            elif count != 'blocked':
                response.midflash = 'Correct, just %s captchas left' % count
            else:
                record_action('blocked')
        else:
            response.midflash = "bad. try again."
            debug('They took a bad guess')
            record_action('bad guess')

    if is_preview():
        submitter = INPUT(_type='submit', _value='Submit', _disabled="true")
    else:
        submitter = INPUT(_type='submit')

    final_word = '<p style="padding-top: 28px;">This is a research study about captchas.  We are not spammers.<br/>The prices and tasks change over time, so try again later if you do not like this task or price.</p>'

    feedback_box = XML('<p>Optional feedback: <input type="text" name="feedback"'
                       + ('disabled=True' if is_preview() else '')
                       + '/></p>')

    checkpoint('ending captcha', True)
    return dict(form=FORM(XML(captcha.displayhtml(captcha_public_key, disabled=is_preview())),
                          submitter,
                          XML(final_word),
                          feedback_box),
                total=request.num_tasks,
                pay=request.price_string)


