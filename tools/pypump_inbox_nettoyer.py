#!/usr/bin/env python

"""
A Python script for using PyPump to cleanup a messy inbox.
Specifically, if there are a bunch of messages you want to delete,
this will do it. Be careful!
"""

import ConfigParser
import argparse
import sys

from pypump import PyPump, Client
from pypump.models.image import Image
from pypump.models.collection import Collection
from pypump.models.collection import Public
from pypump.models.person import Person
from pypump.exception import PyPumpException


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
print(testrun)
nmessages=args.nmessages
pattern = args.pattern
yestoall = (args.yestoall == 1)
config = ConfigParser.ConfigParser()
config.read(args.config)

webfinger = config.get('global', "webfinger")
client_credentials = config.get('global', 'client_credentials').split(',')
client_tokens = config.get('global','client_tokens').split(',')

def simple_verifier(url):
    print 'Go to: ' + url
    return raw_input('Verifier: ') # they will get a code back

client = Client(
    webfinger=webfinger,
    name="PyPump",
    type="native",
    key=client_credentials[0], # client key
    secret=client_credentials[1] # client secret
)
pump = PyPump(
    client=client,
    token=client_tokens[0], # the token key
    secret=client_tokens[1], # the token secret
    verifier_callback=simple_verifier
)

print("Loading pump.io inbox for %s" % webfinger)
print("   the name on this inbox is: %s" % pump.me)

failed_deleted = []

my_inbox = pump.me.inbox
for activity in my_inbox.major[:nmessages]:

    if activity.obj.deleted:
        continue

    # determine if this message matches the patterns
    if activity.obj.content.find(pattern) != -1:
        print("Message contains pattern:")
        print("   pattern: %s" % pattern)
        print("   content: %s" % activity.obj.content)
        print("    msg id: %s" % activity.id)
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
                activity.obj.delete()
            except pypump.exception.PyPumpException:
                print("There was a PyPump error. Unable to delete message %s" % activity.id)
                failed_deleted.append(activity.id)
        pass
    pass


print("The following messages had errors upon attempt to delete:")
print(failed_deleted)
