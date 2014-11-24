import json
import re
import time
import urllib
import urllib2
import MySQLdb
from HTMLParser import HTMLParser
from errbot import BotPlugin, botcmd
from config import LOG_CHATS


class Fun(BotPlugin):

    def activate(self):
        super(Fun, self).activate()
        self.yt_regex = re.compile(
            '(youtube.com/watch\S*v=|youtu.be/)([\w-]+)')

    def get_configuration_template(self):
        return {'db_user': u'',
                'db_pass': u'',
                'db_name': u'',
                'db_host': u''}

    @botcmd
    def yt(self, msg, args):
        searchterm = urllib.quote_plus(args.encode('utf-8'))
        uri = 'https://gdata.youtube.com/feeds/api/videos?v=2&alt=json&max-results=1&q=' + \
            searchterm
        uri = uri.replace(' ', '+')
        video_info = self.ytget(uri)
        if video_info is 'Error':
            return "Pls Friend, No Bad - YouTube was unable to process your search request."

        if video_info['link'] == "N/A":
            return "%s: Those search terms did not return any video." % (msg.getMuckNick(),)

        message = '[YT Search] Title: ' + video_info['title'] + \
            ' | Uploader: ' + video_info['uploader'] + \
            ' | Duration: ' + video_info['length'] + \
            ' | Link: ' + video_info['link']
        # ' | Uploaded: ' + video_info['uploaded'] + \
        # ' | Views: ' + video_info['views'] + \
        # ' | Comments: ' + video_info['comments'] + \
        # ' | Likes: ' + video_info['likes'] + \
        # ' | Dislikes: ' + video_info['dislikes']

        return HTMLParser().unescape(message)

    def callback_message(self, conn, msg):
        if msg.getType() == "groupchat" and msg.getFrom().getNode() + "@" + msg.getFrom().getDomain() in LOG_CHATS:
            self.log_messages(msg)

        match = self.yt_regex.search(msg.getBody())
        if match:
            uri = 'http://gdata.youtube.com/feeds/api/videos/' + \
                match.group(2) + '?v=2&alt=json'
            video_info = self.ytget(uri)

            if video_info is 'Error':
                self.send(msg.getFrom(
                ), "YouTube didn't return any information for the linked video.", message_type=msg.getType())
            else:
                message = '[YT] Title: ' + video_info['title'] + \
                    ' | Uploader: ' + video_info['uploader'] + \
                    ' | Duration: ' + video_info['length']
                # ' | Uploaded: ' + video_info['uploaded'] + \
                # ' | Views: ' + video_info['views'] + \
                # ' | Comments: ' + video_info['comments'] + \
                # ' | Likes: ' + video_info['likes'] + \
                # ' | Dislikes: ' + video_info['dislikes']

                self.send(msg.getFrom(), message, message_type=msg.getType())

    def ytget(self, uri):
        try:
            u = self.get_urllib_object(uri)
            bytes = u.read()
            u.close()
            result = json.loads(bytes)
            if 'feed' in result:
                video_entry = result['feed']['entry'][0]
            else:
                video_entry = result['entry']
        except:
            return 'Error'
        vid_info = {}
        try:
            # The ID format is tag:youtube.com,2008:video:RYlCVwxoL_g
            # So we need to split by : and take the last item
            vid_id = video_entry['id']['$t'].split(':')
            vid_id = vid_id[len(vid_id) - 1]  # last item is the actual ID
            vid_info['link'] = 'http://youtu.be/' + vid_id
        except KeyError:
            vid_info['link'] = 'N/A'

        try:
            vid_info['title'] = video_entry['title']['$t']
        except KeyError:
            vid_info['title'] = 'N/A'

        # get youtube channel
        try:
            vid_info['uploader'] = video_entry['author'][0]['name']['$t']
        except KeyError:
            vid_info['uploader'] = 'N/A'

        # get upload time in format: yyyy-MM-ddThh:mm:ss.sssZ
        try:
            upraw = video_entry['published']['$t']
            # parse from current format to output format: DD/MM/yyyy, hh:mm
            vid_info[
                'uploaded'] = '%s/%s/%s, %s:%s' % (upraw[8:10], upraw[5:7],
                                                   upraw[0:4], upraw[
                    11:13],
                upraw[14:16])
        except KeyError:
            vid_info['uploaded'] = 'N/A'

        # get duration in seconds
        try:
            duration = int(
                video_entry['media$group']['yt$duration']['seconds'])
            # Detect liveshow + parse duration into proper time format.
            if duration < 1:
                vid_info['length'] = 'LIVE'
            else:
                hours = duration / (60 * 60)
                minutes = duration / 60 - (hours * 60)
                seconds = duration % 60
                vid_info['length'] = ''
                if hours:
                    vid_info['length'] = str(hours) + 'hours'
                    if minutes or seconds:
                        vid_info['length'] = vid_info['length'] + ' '
                if minutes:
                    vid_info['length'] = vid_info[
                        'length'] + str(minutes) + 'mins'
                    if seconds:
                        vid_info['length'] = vid_info['length'] + ' '
                if seconds:
                    vid_info['length'] = vid_info[
                        'length'] + str(seconds) + 'secs'
        except KeyError:
            vid_info['length'] = 'N/A'

        # get views
        try:
            views = video_entry['yt$statistics']['viewCount']
            vid_info['views'] = str('{0:20,d}'.format(int(views))).lstrip(' ')
        except KeyError:
            vid_info['views'] = 'N/A'

        # get comment count
        try:
            comments = video_entry['gd$comments']['gd$feedLink']['countHint']
            vid_info['comments'] = str(
                '{0:20,d}'.format(int(comments))).lstrip(' ')
        except KeyError:
            vid_info['comments'] = 'N/A'

        # get likes & dislikes
        try:
            likes = video_entry['yt$rating']['numLikes']
            vid_info['likes'] = str('{0:20,d}'.format(int(likes))).lstrip(' ')
        except KeyError:
            vid_info['likes'] = 'N/A'
        try:
            dislikes = video_entry['yt$rating']['numDislikes']
            vid_info['dislikes'] = str(
                '{0:20,d}'.format(int(dislikes))).lstrip(' ')
        except KeyError:
            vid_info['dislikes'] = 'N/A'
        return vid_info

    def get_urllib_object(self, uri):
        """Return a urllib2 object for `uri` and `timeout` and `headers`.

        This is better than using urrlib2 directly, for it handles redirects, makes
        sure URI is utf8, and is shorter and easier to use.  Modules may use this
        if they need a urllib2 object to execute .read() on.

        For more information, refer to the urllib2 documentation.

        """
        try:
            uri = uri.encode("utf-8")
        except:
            pass
        headers = None
        original_headers = {
            'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (Willie)'}
        if headers is not None:
            original_headers.update(headers)
        else:
            headers = original_headers
        req = urllib2.Request(uri)
        try:
            u = urllib2.urlopen(req, None, 20)
        except urllib2.HTTPError, e:
            # Even when there's an error (say HTTP 404), return page contents
            return e.fp

        return u

    def log_messages(self, msg):
        dbhost = str(u'localhost')
        dbuser = str(u'logger')
        dbpass = str(u'logger')
        dbname = str(u'r2')
        db = MySQLdb.connect(
            host=dbhost, user=dbuser, passwd=dbpass, db=dbname)
        cur = db.cursor()

        channel = msg.getFrom().getNode()
        server = msg.getFrom().getDomain()
        sender = msg.getMuckNick()
        message = msg.getBody()
        now = time.time()

        cur.execute("INSERT INTO chat_logs(`room`, `server`, `sender`, `body`) VALUES (%s, %s, %s, %s)",
                    (channel, server, sender, message))
        db.commit()
        db.close()
        print "[%s] (%s@%s) %s: %s" % (now, channel, server, sender, message)
