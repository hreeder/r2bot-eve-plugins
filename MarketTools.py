import sqlite3
import urllib
from BeautifulSoup import BeautifulSoup
from errbot import BotPlugin, botcmd
from config import SDE_SQLITE


class MarketTools(BotPlugin):

    @botcmd()
    def pc(self, msg, args):
        '''Price checks a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args)

    @botcmd
    def plex(self, msg, args):
        '''Gives the Jita prices for PLEX'''
        return self.priceCheck(usr=msg.mucknick, item="30 Day Pilot's License Extension (PLEX)", system="Jita")

    @botcmd
    def plesk(self, msg, args):
        '''Gives the Jita prices for PLEX'''
        return self.priceCheck(usr=msg.mucknick, item="30 Day Pilot's License Extension (PLEX)", system="Jita")

    @botcmd
    def jita(self, msg, args):
        '''Gives the Jita price for a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args, system="Jita")

    @botcmd
    def rens(self, msg, args):
        '''Gives the Rens price for a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args, system="Rens")

    @botcmd
    def dodixie(self, msg, args):
        '''Gives the Dodixie price for a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args, system="Dodixie")

    @botcmd
    def amarr(self, msg, args):
        '''Gives the Amarr price for a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args, system="Amarr")

    @botcmd
    def hek(self, msg, args):
        '''Gives the Hek price for a specified item'''
        return self.priceCheck(usr=msg.mucknick, item=args, system="Hek")

    def priceCheck(self, usr, item, system=None):
        if len(item) == 0:
            return "You must specify an item to search for"
        conn = sqlite3.connect(SDE_SQLITE)
        cur = conn.cursor()

        cur.execute(
            "SELECT typeID, typeName FROM invTypes WHERE typeName = ? AND published = 1", (item,))
        data = cur.fetchone()

        if not data:
            cur2 = conn.cursor()
            cur2.execute(
                "SELECT typeID, typeName FROM invTypes WHERE typename LIKE ?  AND published = 1 LIMIT 5", ("%" + item + "%", ))
            allitems = cur2.fetchall()
            cur2count = len(allitems)

            if cur2count == 0:
                return "Sorry, I was unable to find anything while searching for %s" % (item,)
            elif cur2count > 1:
                items = []
                for row in allitems:
                    items.append(row[1])
                return "%s: Multiple items were found from that search - %s" % (usr, ', '.join(items))
            else:
                data = allitems[0]

        typeID = data[0]
        typeName = data[1]

        url = ""
        if system:
            systemID = self.systemNameToID(system)
            url = "http://api.eve-central.com/api/marketstat?usesystem=%s&typeid=%s" % (
                str(systemID), str(typeID))
        else:
            url = "http://api.eve-central.com/api/marketstat?typeid=%s" % (
                str(typeID),)

        xml = BeautifulSoup(urllib.urlopen(url))
        buy = xml.marketstat.type.buy.max.string
        sell = xml.marketstat.type.sell.min.string
        buy = float(buy)
        sell = float(sell)

        place = "Global"
        if system:
            place = system.title()
        return "%s (%s) - Buy: %s ISK / Sell: %s ISK" % (typeName, place, '{:,.2f}'.format(buy), '{:,.2f}'.format(sell))

    def systemNameToID(self, systemName):
        systemids = {
            "jita": 30000142,
            "rens": 30002510,
            "dodixie": 30002659,
            "amarr": 30002187,
            "hek": 30002053
        }
        if systemids[systemName.lower()]:
            return systemids[systemName.lower()]
        else:
            return None
