This python script is run locally on your machine hosting the dispatcharr docker files.  This script will take the m3u channel list file from your provider, scrape all the event channels and then create an epg file from them.  It will then place the epg file in the dispatcharr epg folder.  Dispatcharr will then pickup and auto-create an entry for the new epg in the M3U & EPG Manager list.  It will then update it every time you run this script.

Few things to know:
1. My current provider formats the channels a certain way, so you may need to edit the script to change the channel string or just set it to allow for anything.
2. Change the Input file path to point to the m3u file you are downloading from your provider ( channel list )
3. Change the Output file path at the top to point to your docker container files path, if you use ubuntu and snap, you dont have to change it

I recommend creating a basic bash script to download the providers m3u file and then run this script.  You can then run the bash script via crontab a few times a day to ensure event channels get updated.

Simple Bash script(Note i created a sub folder under root called epg for processing)( Command to create file: nano eventepg ):
#!/bin/sh
cd /root/epg/
wget --user-agent=Mozilla --max-redirect=20 --trust-server-names -O providerm3ufile.m3u "<fullproviderURLform3ufilehere>"
/root/event2guide.py

Save the file ( as eventepg ) and make it executable ( chmod +x eventepg )

Crontab ( crontab -e ) entry:
02 10,15,17 * * * /root/eventepg
   
Note, i am assuming you are doing everything from the root folder(cause you are lazy like me), otherwise, change the paths to match where you saved it.
