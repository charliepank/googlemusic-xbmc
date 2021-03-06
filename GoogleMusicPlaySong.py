import sys, time
import simplejson as json

class GoogleMusicPlaySong():

    def __init__(self):
        self.main       = sys.modules["__main__"]
        self.xbmcplugin = self.main.xbmcplugin
        self.xbmcgui    = self.main.xbmcgui
        self.xbmc       = self.main.xbmc
        self.storage    = self.main.storage
        self.prefetch   = self.main.settings.getSetting( "prefetch" )

    def play(self, song_id, params={}):
        song = self.storage.getSong(song_id)

        if song:
            if self.prefetch=="false" or not song[24] or int(self.main.parameters_string_to_dict(song[24]).get('expire'))  < time.time():
                 self.main.log("Prefetch disabled or URL invalid or expired :")
                 url = self.__getSongStreamUrl(song_id)
            else:
                 url = song[24]

            li = self.createItem(song)
        else:
            self.main.log("Track not in library :: "+repr(params))
            if params:
                label=params.get('title')
            li = self.xbmcgui.ListItem(label)
            li.setProperty('IsPlayable', 'true')
            li.setProperty('Music', 'true')
            url = self.__getSongStreamUrl(song_id)


        self.main.log("URL :: "+repr(url))

        li.setPath(url)
        self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=li)

        if self.prefetch=="true":
         try:
            #wait for song playing and playlist ready
            self.xbmc.sleep(10000)
            # get song position in playlist
            get_players = json.loads(self.xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetProperties", "params": {"playerid":0,"properties":["playlistid","position"]},"id": 1}'))
            position = get_players['result']['position']

            # get next song id and fetch url
            get_playlist = json.loads(self.xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.GetItems", "params": {"playlistid":0, "properties": ["file","duration"]}, "id": 1}'))
            self.main.log("Get playlist:: "+repr(get_playlist))

            song_id_next = self.main.parameters_string_to_dict(get_playlist['result']['items'][position+1]['file']).get("song_id")
            self.__getSongStreamUrl(song_id_next)

            # get playing song duration
            duration = get_playlist['result']['items'][position]['duration']
            # stream url expires in 1 minute, refetch to always have a valid one
            while duration > 50:
                self.xbmc.sleep(50000)
                duration = duration - 50
                # test if user manually changed the music
                get_players = json.loads(self.xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetProperties", "params": {"playerid":0,"properties":["playlistid","position"]},"id": 1}'))
                if position != get_players['result']['position']:
                    break
                # before the stream url expires we fetch it again
                self.__getSongStreamUrl(song_id_next)
         except Exception as ex:
            self.main.log("ERROR trying to fetch url: "+repr(ex))
            #raise

    def __getSongStreamUrl(self,song_id):
        import GoogleMusicApi
        self.api = GoogleMusicApi.GoogleMusicApi()
        return self.api.getSongStreamUrl(song_id)

    def createItem(self, song, label=None):
        infoLabels = {
            'tracknumber': song[11],
            'duration': song[21] / 1000,
            'year': song[6],
            'genre': song[14].encode('utf-8'),
            'album': song[7].encode('utf-8'),
            'artist': song[18].encode('utf-8'),
            'title': song[8].encode('utf-8'),
            'playcount': song[15]
        }

        if not label:
            label = song[23]

        if song[22]:
            li = self.xbmcgui.ListItem(label, iconImage=song[22], thumbnailImage=song[22])
        else:
            li = self.xbmcgui.ListItem(label)
        li.setProperty('IsPlayable', 'true')
        li.setProperty('Music', 'true')
        li.setProperty('mimetype', 'audio/mpeg')
        li.setInfo(type='music', infoLabels=infoLabels)

        return li
