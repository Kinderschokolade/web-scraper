from datetime import datetime, timezone
import pandas as pd
import time
import json
import re
import traceback
import random
from dotenv import load_dotenv

# Telegram imports
from telethon import TelegramClient

# Google Colab imports
#from google.colab import files
import os


class TelegramConfig:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv("TELEGRAM_USERNAME")
        self.phone = os.getenv("TELEGRAM_PHONE")
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.max_messages = 10000
        self.time_limit = 3600  # seconds
        self.backup_frequency = 1000


class TelegramScraper:
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.client = TelegramClient('anon', config.api_id, config.api_hash)
        self.total_messages = 0
        self.start_time = None

    async def process_comments(self, channel, message):
        comments_list = []
        try:
            # Get comments using get_messages with reply_to parameter
            async for comment in self.client.iter_messages(
                entity=channel,
                reply_to=message.id,
                limit=None  # Get all replies
            ):
                try:
                    formatted_comment = self._format_comment(channel, comment, message.id)
                    print(formatted_comment)
                    comments_list.append(formatted_comment)
                except Exception as e:
                    print(f'Error formatting comment: {e}')
                    continue
        except Exception as e:
            pass
        return comments_list

    def _format_comment(self, channel, comment, parent_id):
        return {
            'Type': 'comment',
            'Comment Group': channel,
            'Comment Author ID': getattr(comment, 'sender_id', None),
            'Comment Content': remove_unsupported_characters(getattr(comment, 'text', '') or ''),
            'Comment Date': getattr(comment, 'date', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'Comment Message ID': getattr(comment, 'id', None),
            'Comment Author': getattr(comment, 'post_author', None),
            'Comment Views': getattr(comment, 'views', 0),
            'Comment Reactions': self._format_reactions(getattr(comment, 'reactions', None)),
            'Comment Shares': getattr(comment, 'forwards', 0),
            'Comment Media': 'True' if getattr(comment, 'media', None) else 'False',
            'Comment Url': f'https://t.me/{channel}/{parent_id}?comment={getattr(comment, "id", "0")}'.replace('@', '')
        }

    def _format_reactions(self, reactions):
        if not reactions or not hasattr(reactions, 'results'):
            return ''
        try:
            return ' '.join(f"{r.reaction.emoticon} {r.count}" for r in reactions.results)
        except Exception as e:
            print(f'Error formatting reactions: {e}')
            return ''

    def _format_message(self, channel, message, comments_list):
        return {
            'Type': 'text',
            'Group': channel,
            'Author ID': message.sender_id,
            'Content': remove_unsupported_characters(message.text),
            'Date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
            'Message ID': message.id,
            'Author': message.post_author,
            'Views': message.views,
            'Reactions': self._format_reactions(message.reactions),
            'Shares': message.forwards,
            'Media': 'True' if message.media else 'False',
            'Url': f'https://t.me/{channel}/{message.id}'.replace('@', ''),
            'Comments List': remove_unsupported_characters(json.dumps(comments_list))
        }

    def _format_reactions(self, reactions):
        if not reactions:
            return ''
        return ' '.join(f"{r.reaction.emoticon} {r.count}" for r in reactions.results)

    async def scrape_channel(self, channel, keyword, date_min, date_max, file_name='test_scrape'):
        data = []
        channel_count = 0
        offset_id = 0

        try:
            while True:
                if self._should_stop_scraping():
                    print("Stopping due to time or message limit reached")
                    break

                # Get messages in smaller batches with offset
                messages = await self.client.get_messages(
                    entity=channel,
                    limit=100,  # Process in smaller batches
                    offset_id=offset_id,
                    search=keyword
                )

                if not messages:
                    print("No more messages found")
                    break

                for message in messages:
                    if not self._is_message_in_date_range(message, date_min, date_max):
                        print(f"Message date {message.date} outside range {date_min} - {date_max}")
                        continue

                    # Update offset_id for next batch
                    offset_id = message.id

                    # Add rate limiting with small random delay
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                    comments_list = await self.process_comments(channel, message)
                    data.append(self._format_message(channel, message, comments_list))

                    channel_count = self._update_progress(channel, channel_count, message.id, data, file_name)

                    # Backup periodically
                    if channel_count % self.config.backup_frequency == 0:
                        self._create_backup(data, file_name, channel, message.id)

        except Exception as e:
            print(f'{channel} error: {str(e)}')
            traceback.print_exc()  # Print full error traceback
            # Save what we have so far
            self._save_channel_data(data, channel, file_name)

        self._save_channel_data(data, channel, file_name)
        return channel_count

    def _should_stop_scraping(self):
        if self.total_messages >= self.config.max_messages:
            print(f"Reached maximum message limit: {self.config.max_messages}")
            return True

        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.config.time_limit:
            print(f"Reached time limit: {self.config.time_limit} seconds")
            return True

        return False

    def _is_message_in_date_range(self, message, date_min, date_max):
        if not message.date:
            return False

        in_range = date_min <= message.date <= date_max
        if not in_range:
            print(f"Message {message.id} date {message.date} outside range {date_min} - {date_max}")
        return in_range


    def _update_progress(self, channel, count, message_id, data, file_name):
        count += 1
        self.total_messages += 1
        
        print(f'From {channel}: {self.total_messages} with id {message_id}')

        if self.total_messages % self.config.backup_frequency == 0:
            self._create_backup(data, file_name, channel, message_id)
        
        return count

    def _create_backup(self, data, file_name, channel, message_id):
        backup_filename = f'backup_{file_name}_until_{self.total_messages:05}_{channel}_ID{message_id:07}.parquet'
        pd.DataFrame(data).to_parquet(backup_filename, index=False)

    def _save_channel_data(self, data, channel, file_name):
        if data:
            df = pd.DataFrame(data)
            filename = f'complete_{channel}_in_{file_name}_until_{self.total_messages:05}.parquet'
            df.to_parquet(filename, index=False)


def remove_unsupported_characters(text):
    valid_xml_chars = (
        "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD"
        "\U00010000-\U0010FFFF]"
    )
    return re.sub(valid_xml_chars, '', text)


async def main():
    config = TelegramConfig()
    scraper = TelegramScraper(config)
     
    channels = ["CRYPTO_insider_deutscher"]
    keyword = 'BTC'
    date_min = datetime(2023, 1, 1, tzinfo=timezone.utc)
    date_max = datetime.now().replace(tzinfo=timezone.utc)
    
    print(f"Scraping from {date_min} to {date_max}")
    
    scraper.start_time = time.time()
    async with scraper.client:
        for channel in channels:
            try:
                count = await scraper.scrape_channel(channel, keyword, date_min, date_max)
                print(f"\n\n##### {channel} was ok with {count:05} posts #####\n\n")
            except Exception as e:
                print(f"Error processing channel {channel}: {str(e)}")
                traceback.print_exc()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

