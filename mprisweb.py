#!/usr/bin/python

import BaseHTTPServer
#import dbus
import json
import gtk

from quodlibet import app
from quodlibet.plugins.events import EventPlugin
from quodlibet.plugins import PluginConfigMixin

from threading import Thread

#session_bus = dbus.SessionBus()

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

   #proxy_player = session_bus.get_object( 'org.mpris.quodlibet', '/Player' )
   #player = dbus.Interface(
   #   proxy_player,
   #   dbus_interface='org.freedesktop.MediaPlayer'
   #)

   def play_pause( self ):
      #self.player.Pause()
      if app.player.paused:
         app.player.paused = False
      else:
         app.player.paused = True
      return ('text/plain', 'OK')

   def prev( self ):
      #self.player.Prev()
      app.player.previous()
      return ('text/plain', 'OK')

   def next( self ):
      #self.player.Next()
      app.player.next()
      return ('text/plain', 'OK')

   def now_playing( self ):
      return (
         'application/json',
         #'(' + json.dumps( self.player.GetMetadata() ) + ')'
         ''
      )

   def controls( self ):
      return('text/html', '''
<html><head>
<title>Quod Libet</title>
<style type="text/css">
body {
   background: black;
   color: white;
   text-align: center;
}

input {
   background: black;
   color: white;
   padding: 20px;
}
</style>
<script type="text/javascript">
function async_request( url, response_id ) {
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if( 4 == xhttp.readyState && 200 == xhttp.status && null != response_id ) {
         //document.getElementById( response_id ).innerHTML = xhttp.responseText;
         var response = xhttp.responseText;
         console.log( response );
         var response_json = eval( response );
         var out_text = '';
         for( var key in response_json ) {
            if( response_json.hasOwnProperty( key ) ) {
               out_text = out_text + '<dt>' + key + '</dt><dd>' + response_json[key] + '</dd>';
            }
         }
         document.getElementById( response_id ).innerHTML = out_text;
      }
   };
   xhttp.open( "GET", url, true );
   xhttp.send();
}

function refresh_metadata() {
   async_request( '/nowplaying', 'title' );
   setTimeout( function(){ refresh_metadata(); }, 1000 );
}
</script>
</head>
<body>

<div id="controls">
<input type="button" value="&lt;" onClick="async_request( '/prev', null )" />
<input type="button" value="Play" onClick="async_request( '/playpause', null )" />
<input type="button" value="&gt;" onClick="async_request( '/next' )", null />
</div>

<dl id="title"></dl>

<script type="text/javascript">
setTimeout( function(){ refresh_metadata(); }, 1000 );
</script>

</body></html>
''')

   def do_GET( self ):

      try:
         (content_type, response) = {
            '/': self.controls, 
            '/playpause': self.play_pause,
            '/prev': self.prev,
            '/next': self.next,
            '/nowplaying': self.now_playing,
         }[self.path]()

         self.send_response( 200 )
         self.send_header( 'Content-type', content_type )
         self.end_headers()

         self.wfile.write( response )

      except KeyError:
         self.send_response( 404 )
         self.end_headers()

class WebInterface( EventPlugin, PluginConfigMixin ):

   PLUGIN_ID = 'Web Interface'
   PLUGIN_NAME = _('Web Interface')
   PLUGIN_DESC = _('Host a web interface for remote control.')
   PLUGIN_VERSION = '0.4'
   CONFIG_SECTION = 'web_interface'

   DEFAULT_HOSTNAME = '127.0.0.1'
   DEFAULT_PORT = 9000

   httpd = None
   thread = None

   def start_server( self ):
      self.httpd = BaseHTTPServer.HTTPServer(
         (
            self.config_get( 'web_interface_hostname', self.DEFAULT_HOSTNAME ),
            int( self.config_get( 'web_interface_port', self.DEFAULT_PORT) )
         ),
         MyHandler
      )
      thread = Thread( target=self.httpd.serve_forever )
      thread.start()

   def stop_server( self ):
      if None != self.httpd:
         self.httpd.server_close()
      self.httpd = None
      self.thread = None

   def enabled( self ):
      try:
         self.start_server()
      except:
         print( 'server error' )

   def disabled( self ):
      try:
         self.stop_server()
      except:
         print( 'server error' )

   def PluginPreferences( self, parent ):
      def hostname_changed( entry ):
         self.config_set( 'web_interface_hostname', str( entry.get_text() ) )
         self.stop_server()
         self.start_server()

      def port_changed( entry ):
         self.config_set( 'web_interface_port', int( entry.get_text() ) )
         self.stop_server()
         self.start_server()

      vb = gtk.VBox( spacing=10 )
      vb.set_border_width( 10 )

      hbox = gtk.HBox( spacing=6 )
      ve = gtk.Entry()
      ve.set_text( str( self.config_get(
         'web_interface_hostname', self.DEFAULT_HOSTNAME 
      ) ) )
      ve.set_tooltip_text( _( 'Interface address to listen on.' ) )
      ve.connect( 'changed', hostname_changed )
      hbox.pack_start( gtk.Label( _( 'Listen address:' ) ), expand=False )
      hbox.pack_start( ve, expand=False )
      vb.pack_start( hbox, expand=True )

      hbox = gtk.HBox( spacing=6 )
      ve = gtk.Entry()
      ve.set_text( str( self.config_get(
         'web_interface_port', self.DEFAULT_PORT
      ) ) )
      ve.set_tooltip_text( _( 'Port to listen on.' ) )
      ve.connect( 'changed', port_changed )
      hbox.pack_start( gtk.Label( _( 'Listen port:' ) ), expand=False )
      hbox.pack_start( ve, expand=False )
      vb.pack_start( hbox, expand=True )

      vb.show_all()
      return vb

if '__main__' == __name__:

   # TODO: Make it standalone, too!

   pass

