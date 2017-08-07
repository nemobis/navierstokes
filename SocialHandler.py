import abc
__metaclass__  = abc.ABCMeta


import sys
import os
import subprocess
import logging
import unicodedata
import commands
import re
import hashlib
import copy
import URLShortener
import chardet
from sets import Set
from rfc2html import markup


class SocialHandler(object):
    def __init__(self):
        # the list of messages gathered from this
        # social network's feed (e.g. your feed)
        self.messages = []

        # a map of users (strings) from another network
        # to users on this network (really, any old mapping
        # of string you like - good for putting hyperlinks to
        # users for discovery on other networks, or notification
        # purposes.
        self.usermap = {}

        # debug flag
        self.debug = False

        # shorten URLs in message content?
        self.do_url_shortening = False

        # URL shortening config to use
        self.urlShorteningConfig = {}

        # time limit for considering posts in this service (seconds)
        self.max_message_age = 3600

        # set a "no share" keyword that, if present in a message, prevents NS from sharing the message
        self.noshare_keyword = ""

        # check that lynx is installed and accessible
        lynx_check = ""
        try:
            lynx_check = subprocess.check_output(["lynx", "--help"])
        except subprocess.CalledProcessError:
            self.msg(3, self.texthandler("Lynx is required, but I cannot run it. Make sure it is installed and located in the PATH."))
            pass
        except OSError:
            self.msg(3, self.texthandler("Lynx is required, but I cannot run it. Make sure it is installed and located in the PATH."))
            pass


        return

    @abc.abstractmethod
    def gather(self):
        """ This method harvests posts from a social network """

    @abc.abstractmethod
    def write(self,message=unicode("","utf8")):
        """ This method posts a message to a social network """

    def append_message(self, message=unicode("","utf8")):
        # safely append messages
        if self.noshare_keyword != "":
            if message.content.find(self.noshare_keyword) == -1:
                self.messages.append(message)
                pass
            pass
        else:
            self.messages.append(message)
            pass
        return


    def texthandler(self, text=unicode("","utf8")):
        if not isinstance(text, unicode):
            return text.decode('utf8', errors='ignore')
        return text


    def reshare_text(self, owner="someone"):
        """ This method returns common text that can be used to
        prepend to a reshared post"""
        text = self.texthandler("RT from %s" % (owner))
        return text

    def msg(self,level=0,text=unicode("","utf8")):
        level_text = self.texthandler("INFO")
        message = self.texthandler("%s: %s" % (self.__class__.__name__, text))

        if level == 0:
            logging.info(message)
        elif level == 1:
            logging.warning(message)
        elif level == 2:
            logging.error(message)
        elif level == 3:
            logging.critical(message)
            pass

        #print "%s: [%s] %s" % (self.__class__.__name__, level_text, text)


        if level > 2:
            sys.exit()

        return

    def generate_id(self,text=unicode("","utf8")):
        # generate an ID for a message from input text by generating
        # an MD5 checksum from the text

        try:
            message_md5sum = hashlib.md5(text).hexdigest()
        except UnicodeEncodeError:
            message_md5sum = hashlib.md5(text.encode('utf-8')).hexdigest()
            pass

        return int(message_md5sum, 16)



    def map_users(self, text=unicode("","utf8")):
        new_text = text
        for key in self.usermap:
            new_text = new_text.replace(key, self.texthandler('<a href="%s">%s</a>'%(self.usermap[key][0],self.usermap[key][1])))
            pass
        return new_text


    def which(self,program):
        import os
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def changeLinksToURLs(self, msg=unicode("","utf8")):
        prefx       = self.texthandler('<a href="')
        linkClose   = self.texthandler('">')
        postfx      = self.texthandler( '</a>')

        new_msg = unicode("","utf8")
        new_msg += msg

        if not prefx in msg:
            return new_msg
        #<a href="http://www.thisisalink.com/foo/bar.html">this is some link text</a>
        #to
        #this is some link msg http://www.thisisalink.com/foo/bar.html

        pos = 0
        while True:
            pos = new_msg.find(prefx,pos)
            if pos < 0:
                break

            htmlText = new_msg[pos:new_msg.find(postfx,pos) + len(postfx)]

            link = htmlText[htmlText.find(prefx)+len(prefx):htmlText.find(linkClose)]
            linkmsg = htmlText[htmlText.find(linkClose)+len(linkClose):htmlText.find(postfx)]

            outText = linkmsg + ' ' + link

            if linkmsg == link:
                outText = link

            new_msg = new_msg.replace(htmlText, outText)

            pass

        return new_msg

    def HTMLConvert(self, msg=unicode("","utf8") ):
        msg_clean = self.changeLinksToURLs(msg)

        pid = os.getpid()

        htmlfile = open('/tmp/%d_msg.html' % (pid),'w')
        try:
            htmlfile.write( msg_clean )
        except UnicodeEncodeError:
            htmlfile.write( unicodedata.normalize('NFKD', msg_clean).encode('ascii','ignore') )
            pass

        htmlfile.close()

        txt = commands.getoutput('/usr/bin/lynx --dump -width 2048 -nolist /tmp/%d_msg.html' % (pid))

        os.system('rm -f /tmp/%d_msg.html' % (pid))

        return txt


    def TextToHtml(self, msg=unicode("","utf8") ):
        return markup(html_message)


    def T2H_URLs(self, text=unicode("","utf8")):
        html_text = ""

        # Retrieves the urls from this text
        found_urls = list(Set(re.findall(self.texthandler('(?:http[s]*://|www.)[^"\'<> ]+'), text, re.MULTILINE)))

        if len(found_urls) == 0:
            return self.texthandler(text)

        # deep-copy the text and prepare for it to be mangled... politely.
        html_text = copy.deepcopy(text)

        url = unicode("","utf8")

        for url in found_urls:
            try:
                html_text = html_text.replace(url, "<a href=\"%s\">%s</a>" % (url,url))
            except UnicodeDecodeError:
                url = url.encode('utf-8')
                html_text = html_text.replace(url, "<a href=\"%s\">%s</a>" % (url,url))
                pass

            pass


        return html_text

    def ShortenURLs(self, text=unicode("","utf8")):
        # convert all links in HTML to shortened links using a shortening service

        # Get all unique URLs from this text string

        found_urls = list(Set(re.findall(self.texthandler('(?:http[s]*://|www.)[^"\'<> ]+'), text, re.MULTILINE)))

        if len(found_urls) == 0:
            return self.texthandler(text)

        url_shortener = URLShortener.URLShortener(self.urlShorteningConfig)

        new_text = copy.deepcopy(text)

        url = unicode("","utf8")

        for url in found_urls:
            shortened_url = url_shortener.shorten(url)

            try:
                new_text = new_text.replace(url, shortened_url)
            except UnicodeDecodeError:
                url = url.encode('utf-8')
                shortened_url = shortened_url.encode('utf-8')
                new_text = new_text.replace(url, shortened_url)
                pass

            pass

        return new_text
