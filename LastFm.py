import pylast
from errbot import BotPlugin, botcmd


class LastFM(BotPlugin):

    def get_configuration_template(self):
        """Defines the configuration structure this plugin supports

        You should delete it if your plugin doesn't use any configuration like this"""
        return {'API_KEY': u"API_KEY",
                'API_SECRET': u"SECRET_KEY"
                }

    @botcmd
    def np(self, msg, args):
        network = pylast.LastFMNetwork(
            api_key=str(self.config['API_KEY']), api_secret=str(self.config['API_SECRET']))
        user = network.get_user(args)
        try:
            track = user.get_now_playing()
            if track:
                return "[LastFM] %s is currently listening to %s - %s" % (user.name, track.artist.name, track.title)
            else:
                return "[LastFM] %s is not currently scrobbling" % (user.name,)
        except pylast.WSError:
            return "[LastFM] Could not find the user %s" % (args)
