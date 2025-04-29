import logging
from pyrogram import filters
from pyrogram.types import Message
from config import MUSIC_COMMANDS
from utils.youtube import YouTubeDownloader
from utils.helpers import format_queue_message, format_help_message

logger = logging.getLogger("MusicCommands")

def register_music_handlers(client, music_bot):
    """
    Register music bot command handlers
    
    Args:
        client: Pyrogram client
        music_bot: MusicBot instance
    """
    
    @client.on_message(filters.command(MUSIC_COMMANDS['play']))
    async def play_command(client, message: Message):
        """Handle play command"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Extract the song query
            if len(message.command) < 2:
                await message.reply("⚠️ Please provide a YouTube URL or search term!\nUsage: /play [url or search term]")
                return
            
            query = " ".join(message.command[1:])
            
            # Reply with waiting message
            wait_msg = await message.reply("🔍 Searching for your song...")
            
            # Get video info
            video_info = await YouTubeDownloader.get_video_info(query)
            
            if not video_info:
                await wait_msg.edit("❌ No songs found for your query. Please try again with a different search term.")
                return
            
            # Get audio URL
            audio_url = None
            title = None
            
            if 'url' in video_info:
                # For direct URL input
                audio_url, title = await YouTubeDownloader.get_audio_url(video_info['url'])
            else:
                # For search results
                audio_url, title = await YouTubeDownloader.get_audio_url(video_info['id'])
            
            if not audio_url or not title:
                await wait_msg.edit("❌ Couldn't extract audio from this video. Please try another one.")
                return
            
            # Get queue manager for this chat
            queue_manager = music_bot.get_queue_manager(chat_id)
            
            # If nothing is playing, play this song directly
            current_song = music_bot.get_now_playing(chat_id)
            if not current_song:
                if await music_bot.play_song(chat_id, audio_url, title):
                    await wait_msg.edit(f"🎵 Added to queue: **{title}**\n\n⚠️ Note: Actual audio playback is disabled in this version.")
                else:
                    await wait_msg.edit("❌ Failed to add the song. Please try again.")
                return
            
            # Add to queue
            position = queue_manager.add({'url': audio_url, 'title': title})
            if position < 0:
                await wait_msg.edit("❌ Queue is full! Please try again later.")
                return
            
            await wait_msg.edit(f"✅ Added to queue at position #{position}: **{title}**\n\n⚠️ Note: Actual audio playback is disabled in this version.")
        except Exception as e:
            logger.error(f"Error in play_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['pause']))
    async def pause_command(client, message: Message):
        """Handle pause command"""
        try:
            chat_id = message.chat.id
            
            # Check if something is playing
            if not music_bot.get_now_playing(chat_id):
                await message.reply("❌ Nothing is currently in the queue.")
                return
            
            # Pause the playback (will show disabled message)
            await music_bot.pause(chat_id)
        except Exception as e:
            logger.error(f"Error in pause_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['resume']))
    async def resume_command(client, message: Message):
        """Handle resume command"""
        try:
            chat_id = message.chat.id
            
            # Check if something is playing
            if not music_bot.get_now_playing(chat_id):
                await message.reply("❌ Nothing is currently in the queue.")
                return
            
            # Resume the playback (will show disabled message)
            await music_bot.resume(chat_id)
        except Exception as e:
            logger.error(f"Error in resume_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['skip']))
    async def skip_command(client, message: Message):
        """Handle skip command"""
        try:
            chat_id = message.chat.id
            
            # Check if something is playing
            if not music_bot.get_now_playing(chat_id):
                await message.reply("❌ Nothing is currently in the queue.")
                return
            
            # Skip the current song
            current_song = music_bot.get_now_playing(chat_id)
            if await music_bot.skip(chat_id):
                await message.reply(f"⏭️ Skipped: **{current_song['title']}**")
            else:
                await message.reply("❌ Failed to skip the current song.")
        except Exception as e:
            logger.error(f"Error in skip_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['stop']))
    async def stop_command(client, message: Message):
        """Handle stop command"""
        try:
            chat_id = message.chat.id
            
            # Check if something is in the queue
            if not music_bot.get_now_playing(chat_id) and music_bot.get_queue_manager(chat_id).is_empty():
                await message.reply("❌ Nothing is currently in the queue.")
                return
            
            # Clear queue and current song
            if await music_bot.leave_voice_chat(chat_id):
                await message.reply("⏹️ Queue cleared.")
            else:
                await message.reply("❌ Failed to clear the queue.")
        except Exception as e:
            logger.error(f"Error in stop_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['queue']))
    async def queue_command(client, message: Message):
        """Handle queue command"""
        try:
            chat_id = message.chat.id
            
            # Get queue for this chat
            queue_manager = music_bot.get_queue_manager(chat_id)
            queue = queue_manager.get_queue()
            current = music_bot.get_now_playing(chat_id)
            
            # Format queue message
            reply = format_queue_message(queue, current)
            
            if current or queue:
                reply += "\n\n⚠️ Note: Actual audio playback is disabled in this version."
                
            await message.reply(reply)
        except Exception as e:
            logger.error(f"Error in queue_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['now_playing']))
    async def now_playing_command(client, message: Message):
        """Handle now playing command"""
        try:
            chat_id = message.chat.id
            
            # Get current song
            current = music_bot.get_now_playing(chat_id)
            
            if not current:
                await message.reply("❌ Nothing is currently in the queue.")
                return
            
            await message.reply(f"🎵 **Current song:** {current['title']}\n\n⚠️ Note: Actual audio playback is disabled in this version.")
        except Exception as e:
            logger.error(f"Error in now_playing_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(MUSIC_COMMANDS['help']))
    async def help_command(client, message: Message):
        """Handle help command"""
        try:
            help_message = format_help_message(is_music_bot=True)
            # Add note about disabled voice chat feature
            help_message += "\n\n⚠️ **Note:** Voice chat playback functionality is currently disabled. This bot can search for songs and manage queue, but cannot actually play audio in voice chats."
            await message.reply(help_message)
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    logger.info("Music commands registered")
