# to_csv.py
#
# This converts a JSON file to CSV.
# It's important to note that the resulting file will likely be quite large,
# and you probably won't be able to open it in Excel or another CSV reader.
#
# Arguments are: inputfile, outputfile, fields
# Call this like:
# python to_csv.py wallstreetbets_submissions.json wallstreetbets_submissions.csv author,selftext,title

import os
import json
import sys
import csv
from datetime import datetime
import logging.handlers

# Print current working directory
print("Current working directory:", os.getcwd())

# Subreddit name
subreddit_name = "Silksong"
os.makedirs(f".\data\{subreddit_name}\csv", exist_ok=True)

# Put the path to the input JSON file
input_file_path = rf".\data\raw\{subreddit_name}_comments.json"

# Put the path to the output CSV file
output_file_path = rf".\data\{subreddit_name}\csv\{subreddit_name}_comments.csv"

# Maximum number of entries to write to the CSV file
max_csv_size = 100000

# If you want a custom set of fields, put them in the following list.
# If left empty, the script will use a default set of fields.
fields = []

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def read_lines_json(file_name):
    """Read a plain text JSON file line by line and yield the line along with its position."""
    with open(file_name, 'r', encoding='utf-8') as f:
        while True:
            pos = f.tell()  # Get the current file position
            line = f.readline()  # Read one line from the file
            if not line:
                break
            yield line, pos

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file_path = sys.argv[1]
        output_file_path = sys.argv[2]
        if len(sys.argv) >= 4:
            fields = sys.argv[3].split(",")

    is_submission = "submission" in input_file_path.lower()
    if not len(fields):
        if is_submission:
            fields = ["author", "title", "score", "created", "link", "text", "url"]
        else:
            fields = ["author", "score", "created", "link", "body"]

    file_size = os.stat(input_file_path).st_size
    file_lines, bad_lines = 0, 0
    entries_written = 0  # Counter for entries written to CSV
    line, created = None, None
    output_file = open(output_file_path, "w", encoding='utf-8', newline="")
    writer = csv.writer(output_file)
    writer.writerow(fields)
    try:
        for line, file_bytes_processed in read_lines_json(input_file_path):
            try:
                # Check if we've reached the maximum CSV size
                if entries_written >= max_csv_size:
                    log.info(f"Reached maximum CSV size of {max_csv_size} entries. Stopping conversion.")
                    break
                
                obj = json.loads(line)
                output_obj = []
                for field in fields:
                    if field == "created":
                        value = datetime.fromtimestamp(int(obj['created_utc'])).strftime("%Y-%m-%d %H:%M")
                    elif field == "link":
                        if 'permalink' in obj:
                            value = f"https://www.reddit.com{obj['permalink']}"
                        else:
                            value = f"https://www.reddit.com/r/{obj['subreddit']}/comments/{obj['link_id'][3:]}/_/{obj['id']}/"
                    elif field == "author":
                        value = f"u/{obj['author']}"
                    elif field == "text":
                        if 'selftext' in obj:
                            value = obj['selftext']
                        else:
                            value = ""
                    else:
                        value = obj[field]

                    output_obj.append(str(value).encode("utf-8", errors='replace').decode())
                writer.writerow(output_obj)
                entries_written += 1  # Increment the counter for entries written
                created = datetime.utcfromtimestamp(int(obj['created_utc']))
            except json.JSONDecodeError:
                bad_lines += 1
            file_lines += 1
            if file_lines % 100000 == 0:
                if created is not None:
                    log.info(f"{created.strftime('%Y-%m-%d %H:%M:%S')} : {file_lines:,} : {bad_lines:,} : {(file_bytes_processed / file_size) * 100:.0f}%")
                else:
                    log.info(f"{file_lines:,} : {bad_lines:,} : {(file_bytes_processed / file_size) * 100:.0f}%")
    except KeyError as err:
        log.info(f"Object has no key: {err}")
        log.info(line)
    except Exception as err:
        log.info(err)
        log.info(line)

    output_file.close()
    log.info(f"Complete : {file_lines:,} : {bad_lines:,} : {entries_written:,} entries written")
