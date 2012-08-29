import time, sys, commands, traceback

if sqlitep:
    print 'Using sqlite: No background work!!!'
    debug('Using sqlite: No background work!!!')
    exit()

# LOCK the database

# # Kludgy way
# if commands.getoutput('ps -A -o args= --columns 1000') \
#         .count('-R applications/utility/cron/background_work.py') > 2:
#     logging.debug("XXXX Canceling background cron cause there's already one going")
#     exit()

# Better way
if not db.executesql('select pg_try_advisory_lock(2);')[0][0]:
    debug('CRON: FAILED to get background process lock')
    raise Exception('Somebody else is running background processes')
debug('CRON: got lock')


count = 0
while True:
    count += 1
    debug('b2: Sleeping for the %dth time' % count)
    heartbeat('b2')
    time.sleep(10)
    try:
        debug('Processing launch queue')
        process_launch_queue(); heartbeat('b2')

        debug('Refreshing hits')
        refresh_hit_status(); heartbeat('b2')
        debug('Done refreshing hits')
    except KeyboardInterrupt:
        break
    except:
        logger.error("Error in background process2: %s\n%s"
                      % (str(sys.exc_info()[1]),
                         ''.join(traceback.format_tb(sys.exc_info()[2]))))

        
