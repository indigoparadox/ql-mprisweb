#!/usr/bin/python

import BaseHTTPServer
import logging
import dbus
import json

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 9000

session_bus = dbus.SessionBus()

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

   proxy_player = session_bus.get_object( 'org.mpris.quodlibet', '/Player' )
   player = dbus.Interface(
      proxy_player,
      dbus_interface='org.freedesktop.MediaPlayer'
   )

   def play_pause( self ):
      self.player.Pause()
      return ('text/plain', 'OK')

   def prev( self ):
      self.player.Prev()
      return ('text/plain', 'OK')

   def next( self ):
      self.player.Next()
      return ('text/plain', 'OK')

   def now_playing( self ):
      return (
         'application/json',
         '(' + json.dumps( self.player.GetMetadata() ) + ')'
      )

   def controls( self ):
      return('text/html', '''
<html><head>
<title>Quod Libet</title>
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

      logger = logging.getLogger( 'mprisweb.server.get' )

      try:
         (content_type, response) = {
            '/': self.controls, 
            '/playpause': self.play_pause,
            '/prev': self.prev,
            '/next': self.next,
            '/nowplaying': self.now_playing,
         }[self.path]()

         logger.debug( 'Path: {}'.format( self.path ) )

         self.send_response( 200 )
         self.send_header( 'Content-type', content_type )
         self.end_headers()

         self.wfile.write( response )

      except KeyError:
         self.send_response( 404 )
         self.end_headers()

if '__main__' == __name__:

   logging.basicConfig( level=logging.DEBUG )
   logger = logging.getLogger( 'mprisweb.main' )
   
   httpd = BaseHTTPServer.HTTPServer( (HOST_NAME, PORT_NUMBER), MyHandler )
   logger.info( 'Server listening: {}:{}'.format( HOST_NAME, PORT_NUMBER ) )
   try:
      httpd.serve_forever()
   except KeyboardInterrupt:
      pass
   httpd.server_close()

