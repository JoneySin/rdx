from pathlib import Path


class script(object):
    
    START_TXT = """<b>🎬 Hey {}, {}!</b>

<blockquote><b>⚡ Welcome to RdxTv — Next-Gen Cloud Cinema & Series Hub</b></blockquote>

╭━━━〔 🌌 <b>RdxTv Core Experience</b> 〕━━━╮
┃ 📱 <b>RdxTv Mini App</b> — Instant Vault Search
┃ 🎥 <b>Cinema Player</b> — Smooth 10s Skip & Seek
┃ 🌐 <b>Web Portal</b> — Curated Series, Posts & Cast
┃ ⚡ <b>Direct Byte-Stream</b> — Zero-Wait HD Playback
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

<i>Tap <b>Launch RdxTv Hub</b> or send any Movie / Series title below to stream instantly! 🚀</i>"""

    STATUS_TXT = """<b>🛰️ RdxTv System Telemetry</b>

╭━━━〔 👥 <b>Audience & Reach</b> 〕━━━╮
┃ 👤 <b>Users:</b> <code>{}</code>  │  🏘️ <b>Groups:</b> <code>{}</code>
┃ 💎 <b>VIP Members:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〔 🗄️ <b>RdxTv Media Vaults</b> 〕━━━╮
┃ 📦 <b>Total Indexed:</b> <code>{}</code>
┃ 🎬 <b>Primary Vault:</b> <code>{}</code> <i>(🖼️ {})</i>
┃ ☁️ <b>Cloud Vault:</b> <code>{}</code> <i>(🖼️ {})</i>
┃ 🗄️ <b>Archive Vault:</b> <code>{}</code> <i>(🖼️ {})</i>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〔 🎭 <b>Directory & Studio</b> 〕━━━╮
┃ 🌟 <b>Profiles:</b> <code>{}</code> <i>(🎭 {} │ 📱 {} │ 🌐 {})</i>
┃ 🎞️ <b>Posts:</b> <code>{}</code> <i>(🎬 {} │ 📺 {} │ 📱 {} │ 🔞 {})</i>
┃ 🖼️ <b>Total Posters:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

⏱️ <b>Engine Uptime:</b> <code>{}</code>"""

    USER_STATUS_TXT = """<b>🌐 RdxTv Cloud Library</b>

╭━━━〔 🎞️ <b>Indexed Media</b> 〕━━━╮
┃ 📦 <b>Total Files:</b> <code>{}</code>
┃ 🎬 <b>Primary:</b> <code>{}</code>
┃ ☁️ <b>Cloud:</b> <code>{}</code>
┃ 🗄️ <b>Archive:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〔 🌟 <b>Curated Catalog</b> 〕━━━╮
┃ 🎭 <b>Profiles:</b> <code>{}</code> <i>(👤 {} │ 📱 {} │ 🌐 {})</i>
┃ 📺 <b>Studio Posts:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━╯

⏱️ <b>Uptime:</b> <code>{}</code>"""

    NEW_GROUP_TXT = """#RdxTvGroup
╭━━━〔 🏘️ <b>New Group Connected</b> 〕━━━╮
┃ 📌 <b>Title:</b> {}
┃ 🆔 <b>ID:</b> <code>{}</code>
┃ 🔗 <b>Username:</b> @{}
┃ 👥 <b>Members:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"""

    NEW_USER_TXT = """#RdxTvUser
👤 <b>Name:</b> {}
🆔 <b>ID:</b> <code>{}</code>"""

    NOT_FILE_TXT = """👋 Hello {},

🔎 We couldn't find <b>"{}"</b> in the <b>RdxTv</b> vault yet.

<blockquote>💡 <b>Quick Search Tips:</b>
• Check the exact spelling on Google / IMDb
• Include the release year if needed (e.g. <code>Avatar 2009</code>)
• Avoid extra symbols or emojis</blockquote>"""
    
    FILE_CAPTION = """<b>🎬 {file_name}</b>

<i>⚡ Powered by <b>RdxTv</b></i>"""

    WELCOME_TEXT = """👋 Welcome {mention} to <b>{title}</b>! 🎬
<i>Send any Movie or Series name to search on RdxTv.</i>"""

    HELP_TXT = """<b>⚡ RdxTv Command Center — {}</b>

<blockquote>Select a module below to view user guides, admin controls, and system tools.</blockquote>"""

    ADMIN_COMMAND_TXT = """<blockquote><b>👑 <u>RdxTv Admin Console</u></b></blockquote>

• /stats - Live database &amp; vault telemetry
• /delete - Move file to Recycle Bin
• /delete_all - Clear vault collection
• /web_users - RdxTv Web Portal accounts
{repair_command}• /restart - Restart RdxTv engine
• /sendAll on|off - Toggle Send All group buttons
• /users - Export users.txt backup
• /chats - Export chats.txt backup

<blockquote><b>🛠️ <u>Vault &amp; Chat Maintenance</u></b></blockquote>

• /leave &lt;chat_id&gt; - Disconnect from a chat
• /invite_link &lt;chat_id&gt; - Generate invite link
• /ban_grp | /unban_grp &lt;id&gt; [reason] - Moderate group access
• /ban_user | /unban_user &lt;id&gt; [reason] - Moderate user access
• /check_db - Primary → Cloud vault migration check
• /cancel - Cancel a running /check_db

<blockquote><b>⚙️ <u>Group Controls</u></b></blockquote>

• /search - Auto Filter search
• /settings - Group filter settings
• /button_style - Inline result button style""".replace(
        "{repair_command}",
        "• /repair_library - Refresh thumbnails &amp; migrate metadata (temporary)\n"
        if (Path(__file__).parent / "plugins" / "repair_library_TEMP.py").is_file() else "",
    )

    PLAN_TXT = """<b>💎 RdxTv VIP Membership 💎</b>

<blockquote>Unlock instant ad-free streaming, priority multi-vault search, and full access to the <b>RdxTv Web Cinema</b> portal!</blockquote>

╭━━━〔 ⚡ <b>VIP Rate</b> 〕━━━╮
┃ 💰 <b>Price:</b> <code>₹{} / Day</code>
╰━━━━━━━━━━━━━━━━━━━━╯

<b>📲 How to Activate:</b>
1️⃣ Tap <b>Buy Subscription</b> below and choose your duration.
2️⃣ Complete payment using the generated UPI QR / Pay link.
3️⃣ Send your payment screenshot to {} for instant activation! 🚀"""

    USER_COMMAND_TXT = """<blockquote><b>🎬 <u>RdxTv User Commands</u></b></blockquote>

• /start - Launch RdxTv hub &amp; Mini App
• /id - View Telegram User &amp; Chat ID
• /link - Direct Watch &amp; Download link (reply to media)"""

    LOG_INDEX_TXT = """#RdxTvIndexReport
╭━━━〔 📥 <b>RdxTv Vault Indexer</b> 〕━━━╮
┃ 📢 <b>Channel:</b> {}
┃ 🆔 <b>ID:</b> <code>{}</code>
┃ 🗂️ <b>Vault:</b> <code>#{}</code>
┃ 🔢 <b>Processed:</b> <code>{}</code>
┃ ✅ <b>Saved:</b> <code>{}</code>
┃ ♻️ <b>Duplicates:</b> <code>{}</code>
┃ 🚫 <b>Unsupported:</b> <code>{}</code>
┃ ⚠️ <b>Errors:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"""
