from pathlib import Path


class script(object):
    
    START_TXT = """<b>Hey {}, {}!</b>

Welcome to <b>RdxTv</b>. Send any movie or series name to search files."""

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
    
    FILE_CAPTION = """<b>🎬 {file_name}</b>"""

    WELCOME_TEXT = """👋 Welcome {mention} to <b>{title}</b>! 🎬
<i>Send any Movie or Series name to search on RdxTv.</i>"""

    HELP_TXT = """<b>⚡ RdxTv Command Center — {}</b>

<blockquote>Select a module below to view user guides, admin controls, and system tools.</blockquote>"""

    ADMIN_COMMAND_TXT = """<blockquote><b>👑 <u>RdxTv Admin Console</u></b></blockquote>

• /start - Launch Admin Hub &amp; Mini App
• /stats - Live database &amp; vault telemetry
• /link - Direct Watch &amp; Download link (reply to media)
• /id - Inspect User, Chat &amp; Media ID
• /delete - Move file to Recycle Bin
• /delete_all - Clear vault collection
• /sendAll on|off - Toggle Send All group buttons
{repair_command}• /restart - Restart RdxTv engine

<blockquote><b>🛠️ <u>Database Maintenance</u></b></blockquote>

• /check_db - Primary → Cloud vault migration check
• /cancel - Cancel a running /check_db

<blockquote><b>⚙️ <u>Group Controls</u></b></blockquote>

• /search on|off - Toggle group auto-filter search
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
╭━━━〔 📥 <b>RdxTv Indexer</b> 〕━━━╮
┃ 📢 <b>Channel:</b> {}
┃ 🆔 <b>ID:</b> <code>{}</code>
┃ 🗂️ <b>Vault:</b> <code>#{}</code>
┃ 🔢 <b>Processed:</b> <code>{}</code>
┃ ✅ <b>Saved:</b> <code>{}</code>
┃ ♻️ <b>Duplicates:</b> <code>{}</code>
┃ 🚫 <b>Unsupported:</b> <code>{}</code>
┃ ⚠️ <b>Errors:</b> <code>{}</code>
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"""
