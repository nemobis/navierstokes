#!/usr/bin/env python

"""
A Python script for using PyPump to cleanup a messy inbox.
Specifically, if there are a bunch of messages you want to delete,
this will do it. Be careful!
"""

import ConfigParser
import argparse
import sys

import diaspy


parser = argparse.ArgumentParser(description='Cleanup a messy pump.io inbox.')
parser.add_argument('--config', metavar='-c', dest='config',
                    help='a configuration file containing pump.io credentials and webfinger information')
parser.add_argument('--pattern', metavar='-p',dest='pattern',
                    help='the pattern to search for in messages targeting deletion')
parser.add_argument('--yestoall', metavar='-y', dest='yestoall', type=int, default=0,
                    help='automatically say yes to all requested deletions by default')
parser.add_argument('--number', metavar='-n', dest='nmessages', type=int, default=100,
                    help='the number of messages to load and consider in the inbox')
parser.add_argument('--test', metavar='-t', dest='testrun', type=int, default=0,
                    help='test the search without actually deleting anything')

args = parser.parse_args()

testrun=args.testrun
nmessages=args.nmessages
pattern = args.pattern
yestoall = (args.yestoall == 1)
config = ConfigParser.ConfigParser()
config.read(args.config)

webfinger = config.get('global', "webfinger")
password = config.get('global', 'password')

connection = diaspy.connection.Connection(pod='https://%s' % (webfinger.split('@')[1]),username=webfinger.split('@')[0],password=password)

print("Loading Diaspora inbox for %s" % webfinger)

failed_deleted = []

connection.login()
stream = diaspy.streams.Activity(connection)
activity_count = 0

load_trials = 0
max_age=86400
#while len(stream) < nmessages:
#    print ("Stream length, %d, is less than %d - trying to load more activities..." % (len(stream),nmessages))
#    max_age += 3600
#    stream.full(backtime=max_age)
#    if load_trials == 10:
#        break
#    else:
#        load_trials += 1
#        pass
#    pass

print("Acting on a total of %d posts" % len(stream))
for activity in stream:
    if activity_count == nmessages:
        break
    else:
        activity_count += 1
        pass

    # determine if this message matches the patterns
    if activity.__str__().find(pattern) != -1:
        print("Message contains pattern:")
        print("   pattern: %s" % pattern)
        print("   content: %s" % activity.__str__())
        print("    msg id: %s" % activity['id'])
        print("")
        do_delete = False
        if yestoall == True:
            print "Deleting message on server..."
            if testrun == 0:
                pass
                do_delete = True
            else:
                print("   ... test run - no actual deletion")
        else:
            answer = raw_input("Delete? (y is default) [Y/n]")
            if answer == "Y" or answer == "y" or answer == "":
                print "Deleting message on server..."
                if testrun == 0:
                    do_delete = True
                    pass
                else:
                    print("   ... test run - no actual deletion")
            elif answer == "N" or answer == "n":
                print "Saving message on server..."
                pass
            pass
        if do_delete:
            try:
                activity.delete()
            except diaspy.errors.PostError:
                print("There was a diaspy error. Unable to delete message %s" % activity.id)
                failed_deleted.append(activity['id'])
        pass
    pass


print("The following messages had errors upon attempt to delete:")
print(failed_deleted)
