# -*- coding: latin-1 -*-
import datetime
import json
import time
import urllib
import urllib2

from errbot import BotPlugin, botcmd


class Time(BotPlugin):

    @botcmd
    def evetime(self, msg, args):
        '''Returns the current evetime'''
        return "%s: It is currently %s EVE" % (msg.mucknick, time.strftime("%H:%M", time.gmtime()))

    def geocode(self, msg, args):
        geocode_endpoint = "http://maps.googleapis.com/maps/api/geocode/json"
        geocoder_args = {
            'sensor': 'false',
            'address': args
        }

        geocode_uri = geocode_endpoint + "?" + urllib.urlencode(geocoder_args)
        geocode_response = urllib2.urlopen(geocode_uri)
        geocoder = json.load(geocode_response)

        if geocoder[u'status'] == u'ZERO_RESULTS':
            return "%s: I was unable to find that location." % (msg.mucknick,)

        geocoded = geocoder['results'][0]

        return geocoded

    @botcmd
    def time(self, msg, args):
        '''Returns the time in a specified city'''
        timezone_endpoint = "https://maps.googleapis.com/maps/api/timezone/json"
        time_endpoint = "http://api.timezonedb.com/"

        geocoded = self.geocode(msg, args)
        if type(geocoded) != dict:
            return geocoded
        latlng = geocoded[u'geometry'][u'location']

        timezoner_args = {
            'sensor': 'false',
            'location': str(latlng[u'lat']) + ',' + str(latlng[u'lng']),
            'timestamp': time.time()
        }

        timezone_uri = timezone_endpoint + "?" + \
            urllib.urlencode(timezoner_args)
        timezone_response = urllib2.urlopen(timezone_uri)
        timezone = json.load(timezone_response)

        tz = timezone[u'timeZoneId']

        time_args = {
            'key': 'BNQ3CH0R4TPN',
            'zone': tz,
            'format': 'json'
        }

        time_uri = time_endpoint + "?" + urllib.urlencode(time_args)
        time_response = urllib2.urlopen(time_uri)
        localtime = json.load(time_response)

        if localtime[u'status'] == u'FAIL':
            return "%s: I was unable to find the time in %s" % (msg.mucknick, geocoded[u'formatted_address'])

        timenow = datetime.datetime.utcfromtimestamp(localtime[u'timestamp'])

        return "%s: It is currently %s in %s || Timezone: %s (%s)" % (msg.mucknick, timenow.strftime("%H:%M"), geocoded[u'formatted_address'], tz, timezone[u'timeZoneName'])

    @botcmd
    def weather(self, msg, args):
        '''Returns the current weather in a specificed location'''
        weather_endpoint = "http://api.openweathermap.org/data/2.5/weather"

        geocoded = self.geocode(msg, args)
        if type(geocoded) != dict:
            return geocoded
        latlng = geocoded[u'geometry'][u'location']

        args = {
            'lat': str(latlng[u'lat']),
            'lon': str(latlng[u'lng']),
            'units': 'metric'
        }

        uri = weather_endpoint + "?" + urllib.urlencode(args)
        response = urllib2.urlopen(uri)
        weather = json.load(response)

        return "%s: The current weather in %s: %s || %s°C || Wind: %s m/s || Clouds: %s%%" % (msg.mucknick, geocoded[u'formatted_address'], weather['weather'][0]['description'], weather['main']['temp'], weather['wind']['speed'], weather['clouds']['all'])
