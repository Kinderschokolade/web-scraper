from datetime import datetime, timezone
import pandas as pd
import time
import json
import re
from dotenv import load_dotenv

# Telegram imports
from telethon import TelegramClient

# Google Colab imports
#from google.colab import files
import os

load_dotenv()
username = os.getenv("TELEGRAM_USERNAME")
phone = os.getenv("TELEGRAM_PHONE")
api_id = os.getenv("TELEGRAM_API_ID") 
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient('anon', api_id, api_hash)

async def scrape_telegram_channel(channels,keyword, date_min, date_max):
    file_name = 'test_scrape' 
    max_t_index = 100000
    time_limit = 60 # 60s 
    filetype = 'parquet'
    me = await client.get_me() # checking my own info
    t_index =0
    start_time = time.time()    

    # Scraping process
    for channel in channels:
        if t_index >= max_t_index:
            break

        if time.time() - start_time > time_limit:
            break

        loop_start_time = time.time()

        data = []

        try:
            c_index = 0
            #async with TelegramClient(username, api_id, api_hash) as client:
            async for message in client.iter_messages(channel, search=keyword):
                try:
                    if date_min <= message.date <= date_max:

                        # Process comments of the message
                        comments_list = []
                        try:
                            async for comment_message in client.iter_messages(channel, reply_to=message.id):
                                comment_text = comment_message.text.replace("'", '"')

                                comment_media = 'True' if comment_message.media else 'False'

                                comment_emoji_string = ''
                                if comment_message.reactions:
                                    for reaction_count in comment_message.reactions.results:
                                        emoji = reaction_count.reaction.emoticon
                                        count = str(reaction_count.count)
                                        comment_emoji_string += emoji + " " + count + " "

                                comment_date_time = comment_message.date.strftime('%Y-%m-%d %H:%M:%S')

                                comments_list.append({
                                    'Type': 'comment',
                                    'Comment Group': channel,
                                    'Comment Author ID': comment_message.sender_id,
                                    'Comment Content': comment_text,
                                    'Comment Date': comment_date_time,
                                    'Comment Message ID': comment_message.id,
                                    'Comment Author': comment_message.post_author,
                                    'Comment Views': comment_message.views,
                                    'Comment Reactions': comment_emoji_string,
                                    'Comment Shares': comment_message.forwards,
                                    'Comment Media': comment_media,
                                    'Comment Url': f'https://t.me/{channel}/{message.id}?comment={comment_message.id}'.replace('@', ''),
                                })
                        except Exception as e:
                            comments_list = []
                            print(f'Error processing comments: {e}')

                        # Process the main message
                        media = 'True' if message.media else 'False'

                        emoji_string = ''
                        if message.reactions:
                            for reaction_count in message.reactions.results:
                                emoji = reaction_count.reaction.emoticon
                                count = str(reaction_count.count)
                                emoji_string += emoji + " " + count + " "

                        date_time = message.date.strftime('%Y-%m-%d %H:%M:%S')
                        cleaned_content = remove_unsupported_characters(message.text)
                        cleaned_comments_list = remove_unsupported_characters(json.dumps(comments_list))

                        data.append({
                            'Type': 'text',
                            'Group': channel,
                            'Author ID': message.sender_id,
                            'Content': cleaned_content,
                            'Date': date_time,
                            'Message ID': message.id,
                            'Author': message.post_author,
                            'Views': message.views,
                            'Reactions': emoji_string,
                            'Shares': message.forwards,
                            'Media': media,
                            'Url': f'https://t.me/{channel}/{message.id}'.replace('@', ''),
                            'Comments List': cleaned_comments_list,
                        })

                        c_index += 1
                        t_index += 1

                        # Print progress
                        current_max_id = min(c_index + message.id, max_t_index)
                        print(f'From {channel}: {c_index:05} contents of {current_max_id:05}')
                        print(f'Total: {t_index:05} contents until now')

                        if t_index % 1000 == 0:
                            backup_filename = f'backup_{file_name}_until_{t_index:05}_{channel}_ID{message.id:07}.parquet'
                            pd.DataFrame(data).to_parquet(backup_filename, index=False)

                        if t_index >= max_t_index:
                            break

                        if time.time() - start_time > time_limit:
                            break

                    elif message.date < date_min:
                        break

                except Exception as e:
                    print(f'Error processing message: {e}')

            print(f'\n\n##### {channel} was ok with {c_index:05} posts #####\n\n')

            df = pd.DataFrame(data)
            partial_filename = f'complete_{channel}_in_{file_name}_until_{t_index:05}.parquet'
            df.to_parquet(partial_filename, index=False)
            # files.download(partial_filename)

        except Exception as e:
            print(f'{channel} error: {e}')

        loop_end_time = time.time()
        loop_duration = loop_end_time - loop_start_time

        if loop_duration < 5:
            time.sleep(60 - loop_duration)


def remove_unsupported_characters(text):
    valid_xml_chars = (
        "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD"
        "\U00010000-\U0010FFFF]"
    )
    cleaned_text = re.sub(valid_xml_chars, '', text)
    return cleaned_text

if __name__=='__main__':
    channels = ["CRYPTO_insider_deutscher"]
    keyword  = 'PERCY'
    date_min = datetime(2023, 1, 1, tzinfo=timezone.utc)
    date_max = datetime.now().replace(tzinfo=timezone.utc) 
    print(date_min, date_max)
    with client:
        client.loop.run_until_complete(
            scrape_telegram_channel(channels, keyword, date_min, date_max)
        )
