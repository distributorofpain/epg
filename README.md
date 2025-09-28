This python script is run locally on your machine hosting the dispatcharr docker files.  This script will take the m3u channel list file from your provider, scrape all the event channels and then create an epg file from them.  It will then place the epg file in the dispatcharr epg folder.  Dispatcharr will then pickup and auto-create an entry for the new epg in the M3U & EPG Manager list.  It will then update it every time you run this script.  The script creates three entries for each event, the first one is the pre-event for the time frame before the event that day, the event itself and then the event is over entry.  Otherwise it just creates one event that says "No Event Today".  You can of course modify what it says in the script however you want as those entries should be pretty straight forward.  I left the channel titles as is for the event itself, minus the main channel name, so it looks exactly how the provider writes it.

Few things to know:
1. My current provider formats the channels a certain way, so you may need to edit the script to change the channel string or just set it to allow for anything.
2. Change the Input file path to point to the m3u file you are downloading from your provider ( channel list )
3. Change the Output file path at the top to point to your docker container files path, if you use ubuntu and snap, you dont have to change it
4. There is a part near the top to set your timezone.
5. There is prerequiste at the top for the timezone setting, make sure to install it on your machine first or the script may error.
6. This assumes all events are 4 hours.  You can edit this in the script ( line 156 or look for "duration_minutes" )
7. This script does not handle events where there is no time specified.  So those will just say "no event today".  Of the test entries i saw, my provider had the same event on a second channel with the time, so i didnt bother handling this ( feel free to submit changes to do so though ).

I recommend creating a basic bash script to download the providers m3u file and then run this script.  You can then run the bash script via crontab a few times a day to ensure event channels get updated.

Simple Bash script(Note i created a sub folder under root called epg for processing)( Command to create file: nano eventepg ):
```
#!/bin/sh
cd /root/epg/
wget --user-agent=Mozilla --max-redirect=20 --trust-server-names -O providerm3ufile.m3u "<fullproviderURLform3ufilehere>"
/root/event2guide.py
```
Save the file ( as eventepg ) and make it executable ( chmod +x eventepg )

Crontab ( crontab -e ) entry:
```
02 4,10,15,17 * * * /root/eventepg
```   
Note, i am assuming you are doing everything from the root folder(cause you are lazy like me), otherwise, change the paths to match where you saved it.


*** VERY IMPORTANT ***
Channel names vary by provider, so you may need to edit this part:

```
# Define a list of regex patterns and their corresponding handler functions
patterns = [
    # Specific Event Channels that dont match the generic chain below due to provider being dumb
    (r'tvg-name="(?P<cname>(MiLB\s?TV\s?★\s?(EVENT)\s?\d*)):?\s*?(?P<ctitle>.*?)?"', parse_event),
    (r'tvg-name="(?P<cname>(TRILLERTV\s?★\s*(Event)\s?\d*)):?\s*?(?P<ctitle>.*?)?"', parse_event),
    # All other Event Channels that can match a generic statement
    (r'tvg-name="(?P<cname>US\s?★\s?(NFL|MLB|MLS|NCAAB|NCAAF|NBA|NHL GAME|UFC|BOXING|EVENT|DAZN|ESPN\+|PEACOCK EVENT|PEACOCK WWE|UFC|BOXING|EVENT)\s?\d*(?: HD|hd)?)(?::?\s?(.*?)?)(?P<ctitle>.*?)?"', parse_event),
]
```

NOTE:  See the names are looking for entries that start with "US ★ " ( note spaces do not have to be present ).  So you may need to change this to match what your provider has listed.  There are three main entry types listed above, if you dont have/use those top two, then you can leave them be, they simply wont match.  For the third entry, this is basically the catch all.  You can add or subtract entries here however you like.  This might even be able to be more simplified. 
NOTE #2: if your provider uses a | or other type of spacer in the name that is not natively supported by regex, it may need to be escaped
