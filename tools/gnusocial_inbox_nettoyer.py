#!/usr/bin/env python

"""
A Python script for using PyPump to cleanup a messy inbox.
Specifically, if there are a bunch of messages you want to delete,
this will do it. Be careful!
"""

import ConfigParser
import argparse
import sys

import xml.dom.minidom
import sys

import subprocess
import os
import re
import codecs
import commands

def texthandler(text=unicode("","utf8")):
    if not isinstance(text, unicode):
        return text.decode('utf8', errors='ignore')
    return text

# functions for handling XML
def get_a_stream(name="out.xml"):
    return xml.dom.minidom.parse(name)

def find_status_elements(doc):
    list_of_status_elements = []
    #print doc.toprettyxml()
    list_of_status_elements = doc.getElementsByTagName("status")
    #print list_of_status_elements
    return list_of_status_elements

def find_element_of_status(status,element_name):
    element_content = ""
    for e in status.childNodes:
        if e.ELEMENT_NODE and e.localName == element_name:
            for t in e.childNodes:
                element_content = t.data.encode('utf-8').strip()
                break
            pass
        pass
    return element_content

def status_author_name(status):
    name = ""
    for e in status.childNodes:
        if e.ELEMENT_NODE and e.localName == "user":
            for u in e.childNodes:
                if u.ELEMENT_NODE and u.localName == "screen_name":
                    for t in u.childNodes:
                        name = t.data.encode('utf-8').strip()
                        break
                    pass
                pass
            pass
        pass
    return name


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



# Get the XML file from the web
print("Loading GNU Social inbox for %s" % webfinger)

username=webfinger.split('@')[0]
server=webfinger.split('@')[1]

try:
    xml_file_contents = unicode(commands.getoutput('curl -m 120 --connect-timeout 60 -s -u \'%s:%s\' https://%s/api/statuses/user_timeline/%s.xml?count=%d' % (username,password,server,username,nmessages)).decode('utf-8'))
except:
    print("Unable to parse the atom file from GNU Social")
    sys.exit()

pid = os.getpid()

dent_file = '/tmp/%d_dents.xml' % (pid)

xml_file = codecs.open(dent_file,'w',encoding='utf-8')
xml_file.write(texthandler(xml_file_contents))
xml_file.close()

document = get_a_stream(dent_file)
dents_xml = find_status_elements(document)

failed_deleted = []

print("...processing %d dents" % (len(dents_xml)))
for dent_xml in dents_xml:

    dent_source = find_element_of_status(dent_xml,"source")
    dent_text = unicode(find_element_of_status(dent_xml,"text").decode('utf8'))
    dent_id = int(find_element_of_status(dent_xml,'id'))
    dent_author = unicode(status_author_name(dent_xml).decode('utf8'))

    if dent_author != webfinger.split('@')[0]:
        continue

    if dent_text.find("deleted notice") != -1:
        continue

    if dent_text.find(pattern) != -1:
        print("Message contains pattern:")
        print("   pattern: %s" % pattern)
        print("   content: %s" % dent_text)
        print("    msg id: %s" % dent_id)
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
                results = commands.getoutput('curl -d -m 120 --connect-timeout 60 -s -u \'%s:%s\' https://%s/api/statuses/destroy/%s.json' % (username,password,server,dent_id))
                print(results)
            except:
                print("There was a GNU Social error. Unable to delete message %s" % activity.id)
                failed_deleted.append(dent_id)
        pass
    pass






print("The following messages had errors upon attempt to delete:")
print(failed_deleted)
