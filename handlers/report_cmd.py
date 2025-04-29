import logging
import re
from pyrogram import filters
from pyrogram.types import Message
from config import REPORT_COMMANDS
from utils.helpers import format_help_message, parse_message_target

logger = logging.getLogger("ReportCommands")

def register_report_handlers(client, report_bot):
    """
    Register report bot command handlers
    
    Args:
        client: Pyrogram client
        report_bot: ReportBot instance
    """
    
    @client.on_message(filters.command(REPORT_COMMANDS['report']))
    async def report_command(client, message: Message):
        """Handle report command"""
        try:
            user_id = message.from_user.id
            
            # Check command format
            if len(message.command) < 3:
                await message.reply(
                    "⚠️ Incorrect format. Use:\n"
                    "/report user <user_id> <reason>\n"
                    "/report message <chat_id>:<message_id> <reason>\n"
                    "/report channel <channel_id> <reason>"
                )
                return
            
            target_type = message.command[1].lower()
            
            if target_type not in ['user', 'message', 'channel']:
                await message.reply("⚠️ Invalid target type. Use 'user', 'message', or 'channel'.")
                return
            
            # Extract target ID and reason
            target_id = message.command[2]
            reason = " ".join(message.command[3:])
            
            if not reason:
                await message.reply("⚠️ Please provide a reason for the report.")
                return
            
            # Validate target based on type
            if target_type == 'user':
                try:
                    target_id = int(target_id)
                except ValueError:
                    await message.reply("⚠️ User ID must be a number.")
                    return
            elif target_type == 'message':
                valid, chat_id, message_id, error = parse_message_target(target_id)
                if not valid:
                    await message.reply(f"⚠️ {error}")
                    return
                target_id = f"{chat_id}:{message_id}"
            elif target_type == 'channel':
                # Ensure channel ID starts with -100 for supergroups/channels
                if not target_id.startswith('-100') and target_id.lstrip('-').isdigit():
                    target_id = f"-100{target_id.lstrip('-')}"
            
            # Create report
            success, result = report_bot.create_report(user_id, target_type, target_id, reason)
            
            if not success:
                await message.reply(f"⚠️ {result}")
                return
            
            report_id = result
            
            # Reply with confirmation
            await message.reply(
                f"✅ Report #{report_id} created successfully!\n"
                f"Type: {target_type}\n"
                f"Target: {target_id}\n"
                f"Reason: {reason}\n\n"
                f"Use /status {report_id} to check the status of your report."
            )
            
            # Send the report
            await report_bot.send_report(report_id)
        except Exception as e:
            logger.error(f"Error in report_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(REPORT_COMMANDS['status']))
    async def status_command(client, message: Message):
        """Handle status command"""
        try:
            # Check command format
            if len(message.command) < 2:
                await message.reply("⚠️ Please provide a report ID. Usage: /status <report_id>")
                return
            
            try:
                report_id = int(message.command[1])
            except ValueError:
                await message.reply("⚠️ Report ID must be a number.")
                return
            
            # Get report status
            report = report_bot.get_report_status(report_id)
            
            if not report:
                await message.reply(f"⚠️ Report #{report_id} not found.")
                return
            
            # Check if user is the report creator
            if report['user_id'] != message.from_user.id:
                await message.reply("⚠️ You can only check the status of your own reports.")
                return
            
            # Format status message
            status_emoji = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }
            
            emoji = status_emoji.get(report['status'], '❓')
            
            status_message = (
                f"{emoji} **Report #{report_id}**\n\n"
                f"Type: {report['target_type']}\n"
                f"Target: {report['target_id']}\n"
                f"Reason: {report['reason']}\n"
                f"Status: {report['status'].upper()}\n"
            )
            
            if report['status'] == 'failed' and 'error' in report:
                status_message += f"Error: {report['error']}\n"
            
            await message.reply(status_message)
        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    @client.on_message(filters.command(REPORT_COMMANDS['help']))
    async def help_command(client, message: Message):
        """Handle help command"""
        try:
            help_message = format_help_message(is_music_bot=False)
            await message.reply(help_message)
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await message.reply(f"❌ An error occurred: {e}")
    
    logger.info("Report commands registered")
