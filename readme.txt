======================================
  How to install and run:
======================================

1. Tell mike to put your ssh public key onto git@yuno.us:~/.ssh/authorized_keys2
2. git clone git@yuno.us:utility
3. cd to utility/ and run ./serve

Now try it out by opening a web browser to http://localhost:8000

You can change settings in models/settings.py.

If you are running in virtualbox but accessing web2py from a browser
on your actual computer then be sure to edit server_url in
settings.py, like:
   server_url = 'computername.local'

At some point, set up a password:
   $ python web2py.py
   choose a password: <put something in here>
   C-c
   $ ./serve


======================================
  Necessary packages
======================================

r-cran-vgam
python-numeric
...?

sudo R
install.packages('censReg', dep = TRUE)


======================================
  Make a Hello World
======================================

Run the webserver with ./serve

Go into controllers/hits.py, and add a function at the bottom
called "my_crazy_hit":

  def my_crazy_hit():
      return {'Hello' : "there"}

Now open a web browser to

  http://yer_computer:yer_port/hits/test/my_crazy_hit

You'll see a fake mechanical turk iframe.  Yeah it looks like the real
thing!

Now inside that iframe is the variables you passed in your controller
function: "Hello" and "there".  Yay, your controller function has a
webpage.  Web2py gives us this handy default view.

Now it's time to make a HTML file to render it.  Go make a
file at views/hits/my_crazy_hit.html and put some stuff in it.

  <h1>This is some stuff</h1>
  And hello {{=hello}} there!

And hit reload and now your hit is connected!  Go forth and develop.

  -------------------------------
  Ok, ready for some handy hints?
  -------------------------------

Write a python line like:

  debug('Hello mister %s', 'jones')

and it will come out into your shell and the file static/log.  This is
conveniently a webpage coming from your web server at

  http://<yersite>/static/debug

  -------------------
  Ok, made something?
  -------------------

Cool.  Now you want to pay people.  You can mark a hit finished with
hit_finished().  This will tell amazon that the turker did it
correctly and should be paid, and logs their completion time to the
database.

The hit will automatically log when it's opened, but you need to say
when it's done.

But you will also want to log mid-hit events.  Like if an important
button is clicked.  You can log anything with:

  log_action('the most important button was just clicked!!!!!!!')

This will all go into a database that you can visualize later.


  -------------------
  Launch it on the Sandbox Site
  -------------------

Open up models/studies.py.  At the top, add a new item to
testing_conditions:

    'my_crazy_hit' : {
        'price' : [.01, .03],
        'style' : ['amazing', 'retarded', 'aphrodesiac']
        }

Now in your controller & view, you can access these variables with

  request.price

and

  request.style == 'amazing':

Each worker will get a different selection from these alternatives.
Now launch a shell and launch a test study with:

  schedule_test_study('my_crazy_hit', 2)

Be sure settings.py had sandbox enabled.  Haha I'm telling you this
after the fact when it can't help you anymore.  Ok so now go to
http://workersandbox.mturk.com and look for your crazy hit.


NOTE ON HIT REQS: (put this somewhere)
  • Your code must work for many may people accessing at a
    time... maybe 10 requests/s.  All parllel.
  • A user might open up to 4 or 5 hits at a time, and do them in
    parallel.


======================================
  Switching to postgres
======================================

The default database is sqlite.  This is great for testing, but it
isn't multithreaded, which means your web app won't allow multiple
people to load pages at the same time, and you can't run cron jobs in
the background.

You should eventually switch to a real database.  We use postgres.
The database lock in cron/background_work.py only works on postgres,
this lock prevents you from running two background_work processes at
the same time (e.g. if you run python web2py twice by accident) which
will likely corrupt your database, and not pay people or something.

 $ sudo apt-get install postgresql
 $ sudo apt-get install python-psycopg2
 $ sudo su postgres
 $ createuser toomim
 Shall the new role be a superuser? (y/n) n
 Shall the new role be allowed to create databases? (y/n) y
 Shall the new role be allowed to create more new roles? (y/n) y
 $ createdb -O toomim utility
 $ createdb -O toomim utility_sandbox
 $ exit
 $ psql utility
 utility=> alter user toomim password 'cranberrypudding';
 utility=> \q

Now edit settings.py and turn sqlite = False, and set the username
and password in database_url.

======================================
  Setting up mail alerts
======================================

You don't need to do this unless you're setting up a live server (the
server you run host real turk jobs from).

Your host needs a public IP, DNS needs to be set up for it, including
MX records.

 $ sudo apt-get install exim4-base exim4-daemon-light
 $ sudo dpkg-reconfigure exim4-config

Choose options:
 - internet site, send & receive email
 - and give it the right hostname

Now /usr/sbin/sendmail should work, and it should be able to send mail.

======================================
  Debugging, etc.
======================================

Make life better:

 $ sudo apt-get install ipython

Type commands and test code

 ./shell.sh

Check out the database:

 psql utility
or
 psql utility_sandbox
or
 sqlite3 utility.db
or
 sqlite3 utility-sandbox.db

======================================
  Launching a real study
======================================

You can launch a test hit or two by clicking the button on /test.

To launch a lot of hits in a real study, open a shell and run:

   schedule_study(num_hits, task, name, description)

For instance,

   schedule_study(100, 'captcha', 'my first captcha study',
                  "picard's log. stardate 2-4-1920. the captchas are
                  under extreme surveillance.  turkers are
                  everywhere. we wish to learn more.")

You might start out small, and then slowly add more hits to the study.

To add more hits, just re-run the schedule_study() function with the
same name, and it will look up your existing study, and just add new
hits to it.

And if anything goes wrong, you can use these functions:
   cancel_unlaunched_hits()
   expire_open_hits()

To get a quick list of all open hits, use open_hits().
To see all studies you've run, use print_studies().

To get an estimate of a study's price, use calc_study_price(num_hits, prices).


======================================
  Hit statuses in the database
======================================

MTurk's statuses are:

  Assignable     -> Nobody is doing it
  Unassignable   -> Somebody is doing it
  Reviewable     -> Somebody finished it
  Reviewing      -> Somebody finished it

And we record them in our database as:

  [mturk status] -> [what we call it]
  Assignable     -> open
  Unassignable   -> getting done
  Reviewable     -> closed
  Reviewing      -> closed

======================================
  Using the Turk Labor Pool
======================================

You'll get very different results if you post the same study twice at
the same time of day -- workers have already seen your hits.  They
might get bored of them.

You might only be able to get some 1,200 participants total on turk,
so you don't want to blow through them all.

Another strategy to keep in mind is posting for indians vs.
americans.  Indians are most active during our night.  Americans
during our day. Indians are very bad at some things, but do lots of
work for very cheap, and there are many of them. If you care about
getting indians vs. americans, you might want to post at a time when
the other ones tend to be asleep. So if you want americans, you can
post at night to get indians.


======================================
  Running the server in the background
======================================

Go ssh into the server, and run:

  screen

Now go run the web2py server.  To disconnect, press

  C-a d
  (that is, control-a and then d)

Now you can log out from the server, whatever.  To get back to your
session, ssh to the server and run

  screen -r

...and you'll be back on it.

======================================
  Using VirtualBox
======================================

Follow the directions in the manual for installing postgresql and
setting up a database.

 - NETWORKING -

After you install ubuntu, you'll want to ssh into your little
computer.  Shut the computer down and open the networking preferences.
Give it another network adapter, make it Host-only.  This is the one
you'll ssh to it on.

On OSX and linux you can access it automatically with
"<computername>.local."  I named my ubuntu computer "lovebox" so now I
can run "ssh lovebox.local." to get into it.

   [If that doesn't work, it might be because zeroconf on ubuntu is
    returning the wrong ip address (e.g. for eth0 instead of eth1).
    Run ifconfig on your ubuntu to see what ip addresses are available
    for each eth0 and eth1.  Try pinging them from your host to see
    which ones you can access.  Then edit your ubuntu's
    /etc/avahi/avahi-daemon.conf and change the lines for
    allow-interfaces and deny-interfaces so that it's returning the
    ethN for the ip address that you're able to see.

    If that doesn't work, you can just ssh to the ip address that
    works, or open your ~/.ssh/config file on your laptop and add
    something like:

    Host = ubuntu
    HostName = 192.168.56.101

    And then you'll be able to just "ssh ubuntu" to log into it.]

Or to mount it as a drive use something like this:

  mkdir /Volumes/Ubuntu
  sshfs toomim@ubuntu /Volumes/Ubuntu -oauto_cache,reconnect,defer_permissions,idmap=user,volname=Ubuntu

If you ever need to renew an ip address, run 'sudo dhclient'.

I also find that this is a good option to have, otherwise when my
laptop switches to a new wireless network, the virtualbox loses dns
access until I reset networking:

    VBoxManage setextradata "Ubuntu" "VBoxInternal/Devices/pcnet/0/LUN#0/Config/DNSProxy" 1


 - OTHER -

Better python shell:
 apt-get install ipython

Then when you run ./shell.sh, you'll get tab completion.  Try this:

  In [1]: turk.<tab>

to see everything in the turk library.

  In [2] (to be continued...)


======================================
  Setting up apache
======================================

You don't need to do this unless you're setting up a live server.

put my file into /etc/apache2/sites-available/utiliscope

sudo apt-get install libapache2-mod-wsgi
sudo a2enmod wsgi
sudo a2ensite utiliscope
sudo /etc/init.d/apache2 restart

======================================
  Setting up database indexes
======================================

Run create_indices_on_postgres().  This is necessary to make things
faster!

======================================
  Backup and load database
======================================

With postgres:
  ./backup
creates a file utility_<date>

On the other computer, go into data/ and run download_todays_db
Then:

  psql utility_sandbox < utility_<date>

======================================
  Resetting a database
======================================

First do:

  ./shell
  db_hash()

Remember what this hash looks like.  You'll use it below.

  dropdb utility_sandbox
  createdb utility_sandbox -O toomim
  rm web2py/applications/utility/databases/<hash>*


======================================
  Web2py migrations
======================================

sqlite cannot drop columns, so it cannot change some constraints like
unique=False

======================================
  Updating web2py
======================================

Download and unzip web2py_src.zip from within the utility/ folder.
It'll overwrite lots of files, but not the utility application.

Now, in web2py/applications/admin/models/access.py, comment out:

  # elif not request.is_local and not DEMO_MODE:
  #     raise HTTP(200, T('Admin is disabled because insecure channel'))

And in web2py/wsgihandler.py, set SOFTCRON = True

======================================
  How transactions work in web2py
======================================

Everything is automatically in a transaction.
So there is never a begin_transaction()!!!
Just a .commit().

Transaction starts as soon as you (read? change?) something.
The web server automatically commits for you when serving the page.
And if something crashes, it calls db.rollback().  Then none of your
database actions actually occur.

However, in modules, scripts, and at the shell, you have to call
db.commit() manually.

-- how transactions work in the databases --

sqlite blocks during a transaction.
so everything will freeze as soon as one process has written a record.

postgres (and others?) just ensure that the data looks consistent.
So changes aren't visible until you call commit.

the transaction technically starts immediately, but in reality it only
matters once you:
  • write to a row with an update
  • use select for_update
  • insert
  • delete

if you're just reading rows, it assumes these don't affect other
transactions

