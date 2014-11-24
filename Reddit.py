import praw
from collections import deque
from requests.exceptions import HTTPError
from errbot import BotPlugin, botcmd


class Reddit(BotPlugin):

    def activate(self):
        super(Reddit, self).activate()
        self.reddit = praw.Reddit(user_agent='example')

        if not self.config:
            self.config['banned_subreddits'] = [u'popping', u'spacedicks']

        self.shown = deque('', 50)

    def get_configuration_template(self):
        return {'banned_subreddits': [u'popping']}

    @botcmd(split_args_with=' ')
    def subreddit(self, msg, args):
        subreddit = str(args[0]).lower().replace("%", "")

        if unicode(subreddit.lower()) in self.config['banned_subreddits']:
            return "NOPE NOT GOING ANYWHERE NEAR THAT, NERD."

        try:
            return self.get_from_subreddit(subreddit)
        except:
            return "Something Bad Happened, I wasn't able to get anything for you. Sorry!"

    @botcmd
    def butt(self, msg, args):
        return self.get_from_subreddit("butts")

    @botcmd
    def boobs(self, msg, args):
        return self.get_from_subreddit("boobs")

    @botcmd
    def cats(self, msg, args):
        return self.get_from_subreddit("cats")

    def get_from_subreddit(self, subreddit):
        subreddit = self.reddit.get_subreddit(subreddit)

        over18 = False
        try:
            over18 = subreddit.over18
        except (HTTPError, praw.errors.InvalidSubreddit), e:
            return "I was unable to find the subreddit '%s'" % subreddit.display_name

        limit = 20
        submissions = subreddit.get_hot(limit=limit)
        shown_count = 1

        for submission in submissions:
            if submission.id not in self.shown and not submission.stickied:
                output = "[/r/" + subreddit.display_name + "] "

                if over18 or submission.over_18:
                    output += ":nws: NSFW | "

                if submission.is_self:
                    output += submission.title + \
                        " | Comments: http://redd.it/" + submission.id
                else:
                    output += submission.title + " | " + submission.url + \
                        " | Comments: http://redd.it/" + submission.id

                if over18 or submission.over_18:
                    output += " | NSFW :nws:"

                self.shown.append(submission.id)

                return output
            elif submission.id in self.shown:
                shown_count += 1

        if shown_count == limit:
            return "That's enough of that subreddit for now. I've pulled all I'm going to right now. Please stop spamming <3"

        return "Something Bad Happened, I wasn't able to get anything for you. Sorry!"
