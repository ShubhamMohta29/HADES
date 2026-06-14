"""Help card HTML rendered inside the chat panel via gui.add_help_card()."""

HELP_HTML = """<div class="help-card">
  <div class="help-title">&#9670;&nbsp; COMMAND REFERENCE</div>

  <div class="help-cat">ACTIVATION</div>
  <div class="help-row"><span class="help-cmd">"HADES"</span><span class="help-desc">wake word</span></div>
  <div class="help-row"><span class="help-cmd">"sleep" / "goodbye" / "stand by"</span><span class="help-desc">enter standby mode</span></div>
  <div class="help-row"><span class="help-cmd">"clear memory"</span><span class="help-desc">reset AI conversation history</span></div>
  <div class="help-row"><span class="help-cmd">"help" / "commands"</span><span class="help-desc">show this reference</span></div>

  <div class="help-cat">INFORMATION</div>
  <div class="help-row"><span class="help-cmd">"weather in [city]"</span><span class="help-desc">current conditions &amp; temp</span></div>
  <div class="help-row"><span class="help-cmd">"news" / "news about [topic]"</span><span class="help-desc">top headlines</span></div>
  <div class="help-row"><span class="help-cmd">"[ticker] stock"</span><span class="help-desc">live stock price</span></div>
  <div class="help-row"><span class="help-cmd">"bitcoin" / "ethereum" / "solana"</span><span class="help-desc">crypto price</span></div>

  <div class="help-cat">SPOTIFY</div>
  <div class="help-row"><span class="help-cmd">"play [song / artist]"</span><span class="help-desc">search and play track</span></div>
  <div class="help-row"><span class="help-cmd">"play my liked songs"</span><span class="help-desc">play liked songs</span></div>
  <div class="help-row"><span class="help-cmd">"play [name] playlist"</span><span class="help-desc">play a specific playlist</span></div>
  <div class="help-row"><span class="help-cmd">"pause" / "skip" / "previous"</span><span class="help-desc">playback control</span></div>
  <div class="help-row"><span class="help-cmd">"what's playing"</span><span class="help-desc">current track info</span></div>
  <div class="help-row"><span class="help-cmd">"shuffle"</span><span class="help-desc">toggle shuffle</span></div>

  <div class="help-cat">PC CONTROL</div>
  <div class="help-row"><span class="help-cmd">"set volume to [%]" / "mute"</span><span class="help-desc">audio control</span></div>
  <div class="help-row"><span class="help-cmd">"open chrome" / "open vscode"</span><span class="help-desc">launch app</span></div>
  <div class="help-row"><span class="help-cmd">"open youtube" / "open github"</span><span class="help-desc">open website</span></div>
  <div class="help-row"><span class="help-cmd">"search for [query]"</span><span class="help-desc">Google search in browser</span></div>
  <div class="help-row"><span class="help-cmd">"screenshot"</span><span class="help-desc">save to Desktop</span></div>
  <div class="help-row"><span class="help-cmd">"battery" / "cpu" / "ram" / "disk"</span><span class="help-desc">system status</span></div>
  <div class="help-row"><span class="help-cmd">"shutdown" / "restart" / "lock"</span><span class="help-desc">power control</span></div>
  <div class="help-row"><span class="help-cmd">"clipboard"</span><span class="help-desc">read clipboard contents</span></div>

  <div class="help-cat">UTILITIES</div>
  <div class="help-row"><span class="help-cmd">"take a note: [text]"</span><span class="help-desc">save a note (asks category)</span></div>
  <div class="help-row"><span class="help-cmd">"read my [category] notes"</span><span class="help-desc">view notes by category</span></div>
  <div class="help-row"><span class="help-cmd">"delete my last note"</span><span class="help-desc">remove the most recent note</span></div>
  <div class="help-row"><span class="help-cmd">"delete my [category] notes"</span><span class="help-desc">remove all notes in a category</span></div>
  <div class="help-row"><span class="help-cmd">"remind me in [N] mins to [task]"</span><span class="help-desc">timed reminder</span></div>
  <div class="help-row"><span class="help-cmd">"what time is it" / "what's today"</span><span class="help-desc">time &amp; date</span></div>

  <div class="help-cat">SCREEN VISION</div>
  <div class="help-row"><span class="help-cmd">"what's on my screen"</span><span class="help-desc">AI screen analysis</span></div>
  <div class="help-row"><span class="help-cmd">"help me with my homework"</span><span class="help-desc">screen-aware assistance</span></div>
</div>"""
