#!/usr/bin/env python3
#apt install python3-tzlocal  (may not be needed any more)
#Print lines are commented out so they can be used for future troubleshooting if an IPTV provider throws in weird crap for the channel title
import re
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import pytz
from tzlocal import get_localzone_name

# Input file path, download this from your provider via curl first, note i created a folder called epg under root
INPUT_M3U_FILEPATH = "/root/epg/INPUTYOURPROVIDERSM3UHERE.m3u"

# Output file path, this will be where dispatcharr is located and it saves it to the epgs folder as event2guide.xml ( change if you dont use ubuntu snap )
OUTPUT_EPG_FILEPATH = "/root/snap/docker/current/dispatcharr_data/epgs/event2guide.xml"

# If you want to test output first, pound out the above entry and use this to see what it looks like.  Also, if you run it manually, it will have screen output that is helpful.
#OUTPUT_EPG_FILEPATH = "/root/epg/output.xml"

# Set the timezone to Eastern Time (EST) - SET YOUR TIMEZONE
local_timezone = pytz.timezone('America/New_York')

def parse_time(time_info_str, today):
    """Parses various time formats and returns a timezone-aware datetime object."""
    parsed_datetime = None
    if not time_info_str:
        return None

    try:
        # First, remove the bracketed text at the end of the string if its there... cause fucking providers.
        temp_time_str = re.sub(r'\s?\[.*?\]$', '', time_info_str.strip(), flags=re.IGNORECASE)

        # First, remove any timezone abbreviations and ignore case cause fucking providers...
        clean_time_str = re.sub(r'\s?(?:ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|PT|PST|PDT|AT|AST|ADT|GMT|UTC|CET|CEST|WET|WEST|BST|EET|EEST|JST|AEST|AEDT)$', '', temp_time_str, flags=re.IGNORECASE)

        # Clean up spaces in the time... cause fucking providers... like WHY would you put a space in 10: 30PM... just fucking why.
        clean_time_str = clean_time_str.replace(": ", ":")

#        print(f"cleantime: {clean_time_str}" )

        # Initialize parsed_time to None.
        parsed_time = None

        #Try all time-only formats first using sequential try...except blocks.  Because the provider cant make up their mind as to which format they want to use!!

            # New: Try 24-hour format with colon (e.g., "14:30")
        try:
            parsed_time = datetime.datetime.strptime(clean_time_str, "%H:%M").time()
        except ValueError:
            pass

        if not parsed_time:
            # New: Try 24-hour format without colon (e.g., "14")
            try:
                parsed_time = datetime.datetime.strptime(clean_time_str, "%H").time()
            except ValueError:
                pass

        # The existing 12-hour try blocks follow
        if not parsed_time:
            try:
            # 1. Try format with colon and space (e.g., "10:30 PM")
                parsed_time = datetime.datetime.strptime(clean_time_str.upper(), "%I:%M %p").time()
            except ValueError:
                pass  # Move to the next format on failure

        if not parsed_time:
            try:
                # 2. Try format with colon and no space (e.g., "10:30PM")
                parsed_time = datetime.datetime.strptime(clean_time_str.upper(), "%I:%M%p").time()
            except ValueError:
                pass

        if not parsed_time:
            try:
                # 3. Try format with no colon (e.g., "8PM")
                parsed_time = datetime.datetime.strptime(clean_time_str.upper(), "%I%p").time()
            except ValueError:
                pass

        if not parsed_time:
            try:
                # 4. Try format with no colon (e.g., "8 PM")
                parsed_time = datetime.datetime.strptime(clean_time_str.upper(), "%I %p").time()
            except ValueError:
                pass



        # If any of the above time formats were successfully parsed, combine and return. Geesh, ridiculous, had to add ignorecase everywhere cause random formatting by provider!
        if parsed_time:
            parsed_datetime = datetime.datetime.combine(today, parsed_time)
            # Localize the parsed datetime object and return
            return local_timezone.localize(parsed_datetime)

        # Now, if a simple time wasn't found, check the other elif patterns.
        elif re.match(r'\d*/\d*\s?(?:AM|PM|A|P)', clean_time_str, re.IGNORECASE):
            # Try format: "12/3PM"
            time_str = re.search(r'\d*/(\d*\s?(?:AM|PM|A|P))', clean_time_str, re.IGNORECASE).group(1)
            parsed_time = datetime.datetime.strptime(time_str.upper(), "%I%p").time()
            parsed_datetime = datetime.datetime.combine(today, parsed_time)

        elif re.match(r'(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)\s?\d*\s?\w{3}\s?\d*:\d*', clean_time_str, re.IGNORECASE):
            # Try format: "Sat 23 Nov 11:00"
            year = datetime.date.today().year
            date_time_str_with_year = f"{time_info_str.strip()} {year}"
            parsed_datetime = datetime.datetime.strptime(date_time_str_with_year, "%a %d %b %H:%M %Y")

        if parsed_datetime:
            # Localize the parsed datetime object and return
            return local_timezone.localize(parsed_datetime)

    except (ValueError, AttributeError):
        return None

    return None

def parse_event(match, today):
    # Get the entire content string to be parsed here becuase the regex was getting insane...
    content = match.group("ctitle").strip()
    cname = match.group("cname").strip()

    # Regex to extract the time from the title
    time_regex_2 = r'(?P<ctime2>(?:(?:\d{1,2}\/\d{1,2}\s)?(?:(?:\d{1,2}:\s?\d{2}|\d{1,2})\s*(?:AM|PM|A|P)|\d{1,2}:\d{2}))(?:\s*(?:ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|PT|PST|PDT|AT|AST|ADT|GMT|UTC|CET|CEST|WET|WEST|BST|EET|EEST|JST|AEST|AEDT))?)'
    time_regex_1 = r'^\s(?P<cignore>\d{1,2}(?::\d{2})?\/)?|(?P<cignore2>\d{1,2}(?::\d{2})?\s*(?:AM|PM|A|P)\/)?(?:(?P<ctime>\d{1,2}(?::\s?\d{2})?\s*(?:AM|PM|A|P))(?:\s*(?:ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|PT|PST|PDT|AT|AST|ADT|GMT|UTC|CET|CEST|WET|WEST|BST|EET|EEST|JST|AEST|AEDT))?)\s?'

    time_info_str = None

    # Setting these here cause doing it below didnt work
    time_match_1 = re.search(time_regex_1, content, re.IGNORECASE)
    time_match_2 = re.search(time_regex_2, content, re.IGNORECASE)
#    print(f"\ncontent: {content}" )
#    print(f"tmatch1: {time_match_1}" )
#    print(f"tmatch2: {time_match_2}" )
    # Corrected if statement: only proceed if the 'ctime' group has a value
    if time_match_1: #and time_match_1.group("ctime"):
        time_info_str = time_match_1.group()
#        print(f"ctime: {time_info_str}" )
    else:
        # If Regex 1 fails, try Regex 2
        if time_match_2:
            time_info_str = time_match_2.group()
#            print(f"ctime2: {time_info_str}" )

            # Use Python logic to separate the date from the time if the idiots drop in a random date in the title(ffs)
            if '/' in time_info_str:
                parts = time_info_str.split(' ', 1)
                # The second part is the time
                time_info_str = parts[1] if len(parts) > 1 else None
            else:
                # No date, so the whole string is the time
                time_info_str = time_info_str
#                print(f"ctime2: {time_info_str}" )

    return {
        "channel_identifier": cname,
        "sport_category": "NFL",
        "title_and_time": content,
        "time_info_str": time_info_str,
        "duration_minutes": 240,
    }

# Define a list of regex patterns and their corresponding handler functions
patterns = [
    # Specific Event Channels that dont match the generic chain below due to provider being dumb
    (r'tvg-name="(?P<cname>(MiLB\s?TV\s?★\s?(EVENT)\s?\d*)):?\s*?(?P<ctitle>.*?)?"', parse_event),
    (r'tvg-name="(?P<cname>(TRILLERTV\s?★\s*(Event)\s?\d*)):?\s*?(?P<ctitle>.*?)?"', parse_event),
    # All other Event Channels that can match a generic statement
    (r'tvg-name="(?P<cname>US\s?★\s?(NFL|MLB|MLS|NCAAB|NCAAF|NBA|NHL GAME|UFC|BOXING|EVENT|DAZN|ESPN\+|PEACOCK EVENT|PEACOCK WWE|UFC|BOXING|EVENT)\s?\d*(?: HD|hd)?)(?::?\s?(.*?)?)(?P<ctitle>.*?)?"', parse_event),
    #(r'tvg-name="(?P<cname>US\s?★\s?(MLS|PEACOCK WWE|EVENT)\s?\d*(?: HD|hd)?)(?::?\s?(.*?)?)(?P<ctitle>.*?)?"', parse_event),
]

def parse_m3u_line(line):
    for pattern, handler in patterns:
        match = re.search(pattern, line)
        if match:
            today = datetime.datetime.now(pytz.utc).astimezone(local_timezone).date()
            event_data = handler(match, today)

            channel_identifier = event_data['channel_identifier']
            sport_category = event_data['sport_category']
            raw_tvg_name = event_data['title_and_time'] # This is just the second part of the tvg-name for now. Needs fixing.

            # Re-extract full tvg-name for description and clean title
            match_full_title_string = re.search(r'tvg-name="([^"]*)"', line)
            original_title = match_full_title_string.group(1).strip() if match_full_title_string else channel_identifier

            #cleaned_event_title = original_title
            #channel_prefix_regex = r"^(US ★\s?(?:NFL|MLB|MLS|NCAAB|NCAAF|NBA|NHL GAME|MiLB TV ★ EVENT|TRILLERTV ★  Event|UFC|BOXING|EVENT|DAZN|ESPN\+|PEACOCK EVENT|PEACOCK WWE|UFC|BOXING|EVENT) \d*(?: HD|hd)?):?\s?"
            #cleaned_event_title = re.sub(channel_prefix_regex, '', cleaned_event_title).strip()
            #time_suffix_regex = r'\s?((?:\d*:?\d*\s?(?:AM|PM|A|P|a|p|am|pm|\w{2}))|(?:\d{1,2}\d*(?:AM|PM|A|P|a|p|am|pm))|(?:(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)\s?\d*\s?\w{3}\s?\d*:?\d*)|(?:\d*\s?(?:AM|PM|A|P|a|p|am|pm)))$'
            #cleaned_event_title = re.sub(time_suffix_regex, '', cleaned_event_title).strip()
            channel_prefix_regex = raw_tvg_name 
            cleaned_event_title = raw_tvg_name
            time_suffix_regex = raw_tvg_name
            original_title = raw_tvg_name
            if not cleaned_event_title:
                cleaned_event_title = "Live Event"

            start_time_local = parse_time(event_data['time_info_str'], today)
            duration_minutes = event_data['duration_minutes']
            print(f"INFO_PRE channel: {channel_identifier}  title: {raw_tvg_name}  Time: {start_time_local}" ),
            all_events = [] # Initialize a list to hold all entries for this line

            if start_time_local and "No Event Today" not in cleaned_event_title:
                # print(f"INFO_START channel: {channel_identifier}  title: {original_title}  Time: {start_time_local}" ),
                # Set duration based on sport category
                if sport_category in ["UFC", "BOXING", "EVENT", "DAZN", "ESPN+", "PEACOCK EVENT", "MiLB TV ★ EVENT", "TRILLERTV ★  Event", "PEACOCK WWE"]:
                    duration_minutes = 240
                elif sport_category in ["NFL", "NCAAF"]:
                    duration_minutes = 240
                elif sport_category in ["MLB"]:
                    duration_minutes = 255
                elif sport_category in ["NCAAB", "NBA", "NHL", "MLS"]:
                    duration_minutes = 210
                else:
                    duration_minutes = 240

                end_time_local = start_time_local + datetime.timedelta(minutes=duration_minutes)

                # 1. Create a placeholder for the time before the event
                pre_event_start = local_timezone.localize(datetime.datetime.combine(today, datetime.time(0, 0)))
                pre_event_duration = (start_time_local - pre_event_start).total_seconds() / 60

                if pre_event_duration > 0:
#                    print(f"INFO_PRE channel: {channel_identifier}  title: {original_title}  Time: {start_time_local}" ),
                    pre_event_entry = {
                        "channel_display_name": channel_identifier,
                        "title": f"Upcoming Event: {cleaned_event_title}",
                        "start_time": pre_event_start,
                        "duration_minutes": pre_event_duration,
                        "tvg_id": channel_identifier,
                        "original_title": f"Upcoming: {original_title}",
                    }
                    all_events.append(pre_event_entry)

                # 2. Append the actual event
#                print(f"INF_OALL channel: {channel_identifier}  title: {original_title}  Time: {start_time_local}" ),
                all_events.append({
                    "channel_display_name": channel_identifier,
                    "title": f"{cleaned_event_title}",
                    "start_time": start_time_local,
                    "duration_minutes": duration_minutes,
                    "tvg_id": channel_identifier,
                    "original_title": original_title,
                })

                # 3. Create a placeholder for the time after the event
                post_event_start = end_time_local
                end_of_day = local_timezone.localize(datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(0, 0)))
                post_event_duration = (end_of_day - post_event_start).total_seconds() / 60

                if post_event_duration > 0:
                    post_event_entry = {
                        "channel_display_name": channel_identifier,
                        "title": "Event concluded, no more events for today.",
                        "start_time": post_event_start,
                        "duration_minutes": post_event_duration,
                        "tvg_id": channel_identifier,
                        "original_title": "Event Concluded",
                    }
                    all_events.append(post_event_entry)

                return all_events

            else:
                # If no event is found, create the "No Event Today" entry
#                print(f"INFO_NO_TIME channel: {channel_identifier}  title: {original_title}  Time: {start_time_local}" ),
                return [{
                    "channel_display_name": channel_identifier,
                    "title": "No Event Today",
                    "start_time": local_timezone.localize(datetime.datetime.combine(today, datetime.time(0, 0))),
                    "duration_minutes": 24 * 60,
                    "tvg_id": channel_identifier,
                    "original_title": "No Event Today",
                }]
    return None

def create_xmltv_for_events(events, filename=OUTPUT_EPG_FILEPATH):
    """
    Generates an XMLTV file from a list of event dictionaries.
    """
    tv = Element("tv", attrib={"generator-info-name": "Custom M3U EPG Script"})
    defined_channels = set()
    counter = 0

    for event in events:
        channel_id = event["tvg_id"]

        if channel_id not in defined_channels:
            channel = SubElement(tv, "channel", id=channel_id)
            display_name = SubElement(channel, "display-name")
            display_name.text = event["channel_display_name"]
            defined_channels.add(channel_id)

        counter += 1
        start_time_xmltv = event["start_time"].astimezone(pytz.utc).strftime("%Y%m%d%H%M%S")
        episode_num_calc = event["start_time"].astimezone(pytz.utc).strftime("%H%M")
        end_time_xmltv = (event["start_time"] + datetime.timedelta(minutes=event["duration_minutes"])).astimezone(pytz.utc).strftime("%Y%m%d%H%M%S")

        unique_channel_key = re.sub(r'[\s★:]+', '-', channel_id).lower()
        episode_num = f"{event['start_time'].strftime('%Y')}·E{episode_num_calc}{counter}"

        programme = SubElement(tv, "programme", attrib={
            "start": start_time_xmltv, 
            "stop": end_time_xmltv,
            "channel": channel_id,
        })

        if "No Event Today" not in event['title']:
            formatted_title = event['title']
        else:
            formatted_title = event['title']

        title = SubElement(programme, "title", lang="en")
        title.text = formatted_title

        desc = SubElement(programme, "desc", lang="en")
        desc.text = f"Live event: {event['title']}"

        episode_num_element = SubElement(programme, "episode-num", system="unique-date-channel")
        episode_num_element.text = episode_num

        category_element = SubElement(programme, "category", lang="en")
        category_element.text = "Sports"

        length_element = SubElement(programme, "length", units="minutes")
        length_element.text = str(event["duration_minutes"])

    xml_string = tostring(tv, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"EPG file '{filename}' created successfully with {len(events)} events.")


def read_m3u_file(filepath):
    all_events = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if 'tvg-name=' in line:
                    parsed_event = parse_m3u_line(line)
                    if parsed_event:
                        all_events.extend(parsed_event)
    except FileNotFoundError:
        print(f"Error: The file at {filepath} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

    return all_events

if __name__ == "__main__":
#    m3u_filepath = "something.m3u"
    events_list = read_m3u_file(INPUT_M3U_FILEPATH)

    if events_list:
        create_xmltv_for_events(events_list, OUTPUT_EPG_FILEPATH)
    else:
        print("No valid events were parsed or the file was not found.")
