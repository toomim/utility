def index():
    request.num_tasks
    width = request.vars.w or request.width
    width = int(width)
    height = 80
    iframe_width = 900
    x = 10
    y = 0
    height = iframe_height - 150

    if request.vars.ajax:
        if request.vars.error == 'true':
            log('AJAX ERROR!!!!!!! it says error=%s' % request.vars.error)

        if request.vars.clicks:
            clicks = sj.loads(request.vars.clicks)
            if len(clicks) == request.num_tasks:
                log('finished this fitts!')
                other_data = dict(clicks=clicks)
                record_action('fitts results', other_data)
                hit_finished(do_redirect=False)
                return sj.dumps({'redirect' : turk_submit_url()})
            
    result = {'left' : '%dpx' % (x),
              'top' : '%dpx' % (y),
              'width' : '%dpx' % (width),
              'height' : '%dpx' % (height),
              'iframe_width' : iframe_width
              }

    record_action('display')
    log('display!')
    return result


def fittsfun ():
    request.num_tasks
    width = 30
    height = 80
    iframe_width = 900
    x = 10
    y = 0
    height = iframe_height - 350

    if request.vars.ajax:
        if request.vars.error == 'true':
            log('AJAX ERROR!!!!!!! it says error=%s' % request.vars.error)

        if request.vars.clicks:
            clicks = sj.loads(request.vars.clicks)
            if len(clicks) == request.num_tasks:
                log('finished this fitts!')
                other_data = dict(clicks=clicks)
                record_action('fitts results', other_data)
                hit_finished(do_redirect=False)
                return sj.dumps({'redirect' : turk_submit_url()})
            
    result = {'left' : x,
              'top' : y,
              'width' : width,
              'height' : height,
              'level' : request.level,
              'iframe_width' : iframe_width
              }

    record_action('display')
    log('display!')
    return result
    
def fittsbomb ():
    request.num_tasks
    width = request.vars.w or 30
    height = 80
    iframe_width = 900
    x = 10
    y = 0
    height = iframe_height - 350

    if request.vars.ajax:
        if request.vars.error == 'true':
            log('AJAX ERROR!!!!!!! it says error=%s' % request.vars.error)

        if request.vars.clicks:
            clicks = sj.loads(request.vars.clicks)
            if len(clicks) == request.num_tasks:
                log('finished this fitts!')
                other_data = dict(clicks=clicks)
                record_action('fitts results', other_data)
                hit_finished(do_redirect=False)
                return sj.dumps({'redirect' : turk_submit_url()})
            
    result = {'left' : x,
              'top' : y,
              'width' : width,
              'height' : height,
              'level' : request.level,
              'iframe_width' : iframe_width
              }

    record_action('display')
    log('display!')
    return result
    
