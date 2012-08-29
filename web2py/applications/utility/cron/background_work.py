import time, sys, commands, traceback
from applications.utility.modules.turk import TurkAPIError

if sqlitep:
    print 'Using sqlite: No background work!!!'
    logging.debug('Using sqlite: No background work!!!')
    exit()

# LOCK the database

# # Kludgy way
# if commands.getoutput('ps -A -o args= --columns 1000') \
#         .count('-R applications/utility/cron/background_work.py') > 2:
#     logging.debug("XXXX Canceling background cron cause there's already one going")
#     exit()

# Better way
if not db.executesql('select pg_try_advisory_lock(1);')[0][0]:
    logging.debug('CRON: FAILED to get background process lock')
    raise Exception('Somebody else is running background processes')
logging.debug('CRON: got lock')


def process_bonus_queue():
    try:
        for row in db().select(db.bonus_queue.ALL):
            heartbeat('b1')
            debug('Processing bonus queue row %s' % row.id)
            try:
                approve_and_bonus_up_to(row.hitid, row.assid, row.worker, float(row.amount), row.reason)
                debug('Success!  Deleting row.')
                db(db.bonus_queue.assid == row.assid).delete()
                if False:
                    worker = db(db.workers.workerid == row.worker).select()[0]
                    worker.update_record(bonus_paid=worker.bonus_paid + float(row.amount))
                db.commit()
            except TurkAPIError as e:
                logger.error(str(e.value))
    except KeyboardInterrupt:
        debug('Quitting.')
        db.rollback()
        raise
    except Exception as e:
        logger.error('BAD EXCEPTION!!! How did this happen? letz rollback and die... ' + str(e))
        try:
            db.rollback()
        except Exception as e:
            logger.error('Got an exception handling even THAT exception: ' + str(e.value))
        raise
    #debug('we are done with bonus queue')

count = 0
while True:
    count += 1
    debug('b1: Sleeping for the %dth time' % count)
    time.sleep(10)
    try:
        heartbeat('b1')
        process_bonus_queue()
    except KeyboardInterrupt:
        break
    except:
        logger.error("Error in background process1: %s\n%s"
                     % (str(sys.exc_info()[1]),
                        ''.join(traceback.format_tb(sys.exc_info()[2]))))

        
