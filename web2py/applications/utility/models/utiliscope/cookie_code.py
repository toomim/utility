def worker_price(ip, prices):
    return hash_to_bucket(ip[:7], prices)
    #return prices[hash_to_bucket(ip, len(prices))]

def update_worker_cookie():
    # First, if we don't have a cookie set, make one up.  It'll be
    # like we had gotten a preview earlier.

    # If we have no workerid (this is a preview), then we can:
    # - get it if it exists in db and we have an existing cookie
    # - else let's just record it in db (but doesn't seem to matter)

    # If we have a workerid:

    # In any case, update that we saw the motherfucker

    def update_cookie(cookieid):
        # First, if we don't have a cookie set, make one up.  It'll be
        # like we had gotten a preview earlier.
        if not cookieid: cookieid = gluon.utils.web2py_uuid()

        # Now get the database entry for this cookie, make one if it
        # doesn't exist.
        cookies_worker = get_one(db.workers.cookieid == cookieid)
        if not cookies_worker:
            log('Making a new cookie')
            db.workers.insert(cookieid = cookieid)
            cookies_worker = get_one(db.workers.cookieid == cookieid)
        return (cookieid, cookies_worker)

    def record_cookie_and_worker(cookieid, workerid):
        worker = get_one((db.workers.cookieid == cookieid)
                         | (db.workers.workerid == workerid))
        if worker:
            worker.update_record(cookieid = cookieid,
                                 workerid = workerid)
        else:
            db.workers.insert(cookieid = cookieid,
                              workerid = workerid)

    workerid = request.vars.workerId
    cookieid = request.cookies.has_key('workercookie') \
        and request.cookies['workercookie'].value

    #if not cookieid and not request.vars.inside_cookie_test:

    log('cookie: hi, cookie is %s', cookieid)
    (cookieid, cookies_worker) = update_cookie(cookieid)
    # Now we have a cookie, and a worker entry for that cookie.

    # If we have no workerid (cause we're in preview), then we can get
    # it from the database:
    if not workerid:
        log('cookie: no worker')
        workerid = cookies_worker.workerid # Might be None, but that's ok
    else:
        log('cookie: worker exists')


        # So, if old cookie is mapped:
        #   - Then check if it's mapped to the new workerid.  If not, they
        #     switched accounts.  If so, we're dandy.
        if cookies_worker and cookies_worker.workerid:
            if cookies_worker.workerid == workerid:
                log('We\'re dandy for worker %s.', workerid)
            else:
                # They switched accounts.
                log('Woah, we thought we had user %s but he switched to %s!',
                    cookies_worker.workerid, workerid)

                ## So the old cookie is bad.  (But these lines don't
                ## actually do anything so I'm commenting them out)
                # old_user_cookieid = cookieid
                # cookieid = None

                # Let's give them the right one.  We might already
                # have one stored in db.
                workers_worker = get_one(db.workers.workerid == workerid)
                if workers_worker and workers_worker.cookieid:
                    cookieid = workers_worker.cookieid
                else:
                    # Give them a fresh cookie
                    (cookieid, cookies_worker) = update_cookie(None)
                    # And map that cookie
                    record_cookie_and_worker(cookieid, workerid)

        else:
            # ... then old cookie is not mapped.
            # Let's check if this was a duplicate cookie that needs to
            # be remapped.  We'll know because workerid already has a
            # cookie.
            workers_worker = get_one(db.workers.workerid == workerid)
            if workers_worker and workers_worker.cookieid:
                # Then we need to remap the old cookie.
                db(db.actions.cookieid == cookieid)\
                    .update(cookieid = workers_worker.cookieid)
                db(db.workers.cookieid == cookieid).delete()
                # And switch to the worker's cookie
                cookieid = workers_worker.cookieid

            else:
                # Otherwise, we need to map this cookie
                record_cookie_and_worker(cookieid, workerid)

    # Let's remember the dude's IP and last-seen date now too
    db((db.workers.workerid == workerid)
       | (db.workers.cookieid == cookieid)) \
       .update(last_seen=now, latest_ip=request.env.remote_addr)
    db.commit()

    request.cookieid = cookieid
    request.workerid = workerid

    # TO DO LATER IF I CARE: If it had a workerid that's different,
    # then we can try updating a couple instances back to the new
    # one... for now who cares let's just leave it as is.

    # Now let's save everything we did in the response so that it'll
    # update the user's web browser.
    response.cookies['workercookie'] = cookieid
    response.cookies['workercookie']['expires'] = 3600 * 24 * 365 * 20 # 20 years
    response.cookies['workercookie']['path'] = '/'
    # Weee we're done!


def junk_code():
    if False:
        # Then we have a workerid.  Now we need to:
        #
        #   1. deal with the fact that we might have been giving
        #      cookies to workers who already had cookies.
        #
        #   2. or update our database if this tells us a workerid
        #      we've been missing

        workers_worker = get_one(db.workers.workerid == workerid)

        # We have three things to worry about:

        # - If someone switched accounts on the same web browser, this
        #   cookie might be for the prior worker

        #   ... so we'll have a workerid, a cookieid, the cookie will
        #   have a worker that isn't this workerid

        # - If a worker logged in on a new web browser, this cookie
        #   is a temporary crapper to replace

        #   ... so we'll have a workerid, a cookieid, this cookie will
        #   have no worker

        # .. I think those are mutually exclusive, but this one can
        # happen with either of them:

        # - If we haven't seen this worker before, we need to add it
        #   to his cookie

        # Did accounts switch on same webbrowser?
        if ((cookies_worker and cookies_worker.workerid != workerid)
            or (workers_worker and workers_worker.cookieid != cookieid)):
            # Then we have a conflict!  There are two types of
            # conflicts.  Either (a) the user logged out and into
            # a new mturk account, or (b) the user signed on with
            # a new web browser, and got a new cookie.
            #
            # In (a), we'll just switch to the new cookie.  In
            # (b), we'll update all his old temporary cookie
            # information to the cookie we have on file.

            log('We have a conflict, %s != %s',
                workers_worker.cookieid, cookieid)
            log('Cookies_worker is %s', cookies_worker)
            if cookies_worker.workerid:
                # Case (a): the worker logged out and into a new
                # mturk account.  This means the browser cookie is
                # associated with the old workerid, and that this
                # is different from the current workerid.
                assert cookies_worker.workerid != workerid, \
                    'Woah nelly, we have %s == %s' % (cookies_worker.workerid, workerid)

                log('Woah, we thought we had user %s but he switched to %s!',
                    cookies_worker.workerid, workerid)

                # This is kind of a weird situation, we might want
                # to set a flag or something, flash something to
                # the user.  But like, what do we do now?

            else:
                # Case (b): the user signed on with a new web
                # browser and has a new cookie... but now we know
                # better, cause he already has a cookie, and we
                # know who he is, so let's use that one.  And
                # let's retroactively revert all his other bunk
                # cookies to this one.
                db(db.actions.cookieid == cookieid)\
                    .update(cookieid = workers_worker.cookieid)
                db(db.workers.cookieid == cookieid).delete()

            # Now let's resolve the conflict by switching the
            # browser's cookie to what we have on file in db (which
            # might be None, in which case we'll need a new one)
            (cookieid, cookies_worker) = update_cookie(workers_worker.cookieid)

        # Now we know we're looking at this worker's cookieid.  Let's
        # make sure the worker is in the database.

        if not workers_worker:
            log('cookie: no workers_worker')
            # If we haven't seen this worker yet, we need to associate
            # it with a cookie.  (There can't be any conflicts if we
            # haven't seen the workerid before.)
            cookies_worker.update_record(workerid = workerid)



#         # Perhaps we've seen this worker before.  In that case, it's
#         # in the DB and has a cookie associated.

#         # Otherwise, we need to associate it with the cookie.

#         if workers_worker and workers_worker.cookieid \
#                 and workers_worker.cookieid != cookieid:
#             # Then we have a cookie stored in our DB, and the
#             # browser's cookie is bunk.  We need to replace its use
#             # with the real cookie.
#             db(db.actions.cookieid == cookieid)\
#                 .update(cookieid = workers_worker.cookieid)
#             db(db.workers.cookieid == cookieid).delete()


#         #  if this cookie hasn't been associated yet
#         if not (cookies_worker and cookies_worker.workerid):
#             # if the worker doesn't have a cookie yet
#             if not workers_worker:
#                 # associate it!
#                 cookies_worker.update_record(workerid = workerid)
#             elif not workers_worker.cookieid:
#                 # Same, but just do an update
#                 workers_worker.update_record(cookieid = cookieid)

#             elif workers_worker.cookieid != cookieid:
#                 # Then we have a worker, with a cookie, and this
#                 # cookie is bunk.  We need to replace its use with the
#                 # real cookie.
#                 db(db.actions.cookieid == cookieid)\
#                     .update(cookieid = workers_worker.cookieid)
#                 db(db.workers.cookieid == cookieid).delete()

#         else:
#             # Then this cookie HAS been associated.  If it's
#             # associated with the right worker, we're fine.
#             # Otherwise, we need to replace it with the cookie for
#             # this worker.

#             if workers_worker.cookieid != cookieid:
#                 cookieid = workers_worker.cookieid

    # Let's remember the dude's IP and last-seen date now too
    db((db.workers.workerid == workerid)
       | (db.workers.cookieid == cookieid)) \
       .update(last_seen=now, latest_ip=request.env.remote_addr)
    db.commit()

    request.cookieid = cookieid
    request.workerid = workerid

    # TO DO LATER IF I CARE: If it had a workerid that's different,
    # then we can try updating a couple instances back to the new
    # one... for now who cares let's just leave it as is.

    # Now let's save everything we did in the response so that it'll
    # update the user's web browser.
    response.cookies['workercookie'] = cookieid
    response.cookies['workercookie']['expires'] = 3600 * 24 * 365 * 20 # 20 years
    response.cookies['workercookie']['path'] = '/'
    # Weee we're done!


def update_worker_cookie2():
    if request.testing:
        request.cookieid = 'fake cookie for tester person'
        return

    # We want a single cookie value for a single workerid.  So every
    # web browser that this workerid uses should have the same cookie
    # value set.

    # The difficult part is (a) we don't know a workerid until they
    # accept a hit, and (b) they might change accounts on the same web
    # browser, and then have an old cookie set.

    existing_cookieid = request.cookies.has_key('workercookie') \
        and request.cookies['workercookie'].value
    cookie_was_unassociated = (existing_cookieid and
                               db(db.workers.cookieid == existing_cookieid).count() == 0)

    if not request.vars.workerId:
        worker = None
    else:
        worker = db(db.workers.workerid == request.vars.workerId).select()
        worker = worker[0] if len(worker) == 1 else None

    #log('Worker is %s, and cookie %s' % (worker, request.vars.workerId))

    # First, let's set the workercookie to something reasonable.  If
    # we know his workerid, let's look it up.  Otherwise, let's use
    # the web browser's cookie if we have it.  Otherwise, let's give
    # him a fresh cookie.
    if worker and worker.cookieid:
        request.cookieid = worker.cookieid
    elif existing_cookieid:
        request.cookieid = existing_cookieid
    else:
        request.cookieid = gluon.utils.web2py_uuid()

    
    # Now, if we just discovered this person's workerId, and it isn't
    # yet in the database...
    if not is_preview() and (not worker or not worker.cookieid):
        # ...then insert the cookied into the worker database
        log('aslkdfjasd')
        if worker:
            log('SFDJSDFJSDJF')
            worker.update_record(cookieid = request.cookieid)
        else:
            log('ZZZZZZZZZZZ')
            db.workers.insert(workerid = request.vars.workerId,
                              cookieid = request.cookieid)

    # Now, if we just discovered this person's workerId (because he
    # went from a preview hit, with no workerid, into an actual
    # assignment), and the browser was already using a cookieid...
    if (request.vars.workerId and existing_cookieid
        # ...and this workerId's cookie is different from the cookie
        # that was in the web browser...
        and existing_cookieid != request.cookieid
        # ... and this cookie value was something we created from
        # scratch, which we know because we haven't associated it
        # with a worker yet...
        and cookie_was_unassociated):
        
        # ...then let's update the existing uses of that cookie to
        # the new cookie!
        db(db.actions.cookieid == existing_cookieid)\
            .update(cookieid = worker.cookieid)

    # If we're switching to a new person
    if (request.vars.workerId and existing_cookieid
        and worker and worker.workerId != request.vars.workerId):
        if cookie_was_unassociated:
            # XXX FIX THIS SHIT
            pass

    # Let's just remember the dude's IP and last-seen date now too
    db((db.workers.workerid == request.vars.workerId)
       | (db.workers.cookieid == request.cookieid)) \
       .update(last_seen=now, latest_ip=request.env.remote_addr)
    db.commit()

    # TO DO LATER IF I CARE: If it had a workerid that's different,
    # then we can try updating a couple instances back to the new
    # one... for now who cares let's just leave it as is.

    # Now let's save everything we did in the response so that it'll
    # update the user's web browser.
    response.cookies['workercookie'] = request.cookieid
    response.cookies['workercookie']['expires'] = 3600 * 24 * 365 * 20 # 20 years
    response.cookies['workercookie']['path'] = '/'
    # Weee we're done!

