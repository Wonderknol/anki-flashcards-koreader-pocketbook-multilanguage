# KOReader → Anki flashcard setup (personal notes)

Last updated: 12 October 2026

This document explains how my ereader-to-Anki flashcard setup works, which files I
changed, and how to put everything back after a plugin update.
It contains no API keys.

---

## 1. What it does

Highlight a word in KOReader and tap **Anki Card**. An AI model writes a card
(definition, synonyms, Dutch translation, a cloze sentence, and the detected
language). The card is saved on the ereader. Later, **Send All Unsent to Anki**
sends everything to Anki as one batch.

```
Ereader (KOReader plugin)
   |--- Wi-Fi --> PC: Anki add-on "gemini_relay" (port 8787) --> Gemini API
   '--- Wi-Fi --> PC: AnkiConnect (port 8765) --> Anki
```

Away from home Wi-Fi, the plugin saves a stub (word, context, book) without calling
the AI. The card text is generated later, at the moment the stub is sent to Anki.

Cards land in deck `KOReader::AI inbox` with these tags: `KOReader`, the book title,
and `lang::<language>` (for example `lang::french`).

---

## 2. Where things live

| What | Where |
|---|---|
| Plugin folder (PocketBook) | `applications/koreader/plugins/AnkiFlashcards.koplugin/` |
| Plugin config + API keys | `configuration.lua` in that folder |
| Saved device settings | `anki_flashcards_settings.json` in `applications/koreader/`. **Overrides `configuration.lua`** |
| Saved cards | `anki_flashcards.json` in `applications/koreader/` |
| Relay add-on (PC) | `%APPDATA%\Anki2\addons21\gemini_relay\` (files: `__init__.py`, `config.json`, `config.md`, `relay.log`) |
| Anki note type | `KOReader AI AnkiFlashcard` (Cloze type) |
| Anki deck | `KOReader::AI inbox` |
| PC address (home network) | `192.168.86.42` (AnkiConnect `:8765`, relay `:8787`) |

Device: a PocketBook ereader running KOReader. To copy files, connect it by USB and
choose the PC-link/USB mode on the device. Its storage then shows up as a drive on the
PC, and KOReader lives in the `applications/koreader/` folder (nothing hidden).
These paths are the standard ones; if KOReader was installed somewhere else,
look for the `koreader` folder that contains `plugins/`.

If the PC's IP address ever changes, update both `anki.url` and `relay_url` in
`configuration.lua`. A DHCP reservation in the router prevents this.

---

## 3. Daily use

- **At home (Wi-Fi on):** highlight a word → **Anki Card**. A short popup shows the
  definition and translation, and the card is saved.
- **Away (Wi-Fi off):** same action. The popup says "Saved for later".
- **Sending:** at home with Anki open: highlight dialog → **Anki Manage → Send All
  Unsent to Anki**. Stubs are generated while sending.
- **Sorting in Anki:** browse deck `KOReader::AI inbox`, or search
  `tag:lang::french`, `tag:lang::italian`, `tag:lang::dutch`.

The relay add-on only runs while Anki is open. If Anki is closed, generation falls
back to a direct call to Google, which is slow (10 to 120 seconds).

---

## 4. Anki side

### Note type `KOReader AI AnkiFlashcard` (Cloze)

Fields, with **Phrase first**:
`Phrase, IPA, Definition, Synonyms, Text, Source, ImageFront, ImageBack, Sound, Translation`

Field names must match exactly. (Having `Text` as the first field caused the early
"failed validation" errors.) IPA, images and Sound are not used any more, but
they stay in the note type because the plugin still sends them.

Front template:

```html
<div class="cloze">{{cloze:Text}}</div>
<div class="hint">{{Definition}}</div>
```

Back template:

```html
<div class="cloze">{{cloze:Text}}</div>
<div class="phrase">{{Phrase}}</div>
<div class="hint">{{Definition}}</div>
{{#Translation}}<div class="trans">{{Translation}}</div>{{/Translation}}
{{#Synonyms}}<div class="syn">≈ {{Synonyms}}</div>{{/Synonyms}}
<div class="source">{{Source}}</div>
```

Styling:

```css
.card { font-family: Arial, sans-serif; font-size: 22px; text-align: center; }
.cloze { margin: 20px 0 12px; }
.phrase { font-size: 26px; font-weight: bold; margin-top: 18px; }
.hint { font-size: 17px; opacity: 0.75; font-style: italic; }
.trans { margin-top: 12px; font-weight: bold; color: #e8a33d; }
.syn { margin-top: 8px; font-size: 18px; }
.source { margin-top: 20px; font-size: 12px; opacity: 0.5; }
```

(These are the templates as first written. Check Tools → Manage Note Types → Cards
for what is actually in use.)

### AnkiConnect

The ereader reaches AnkiConnect over the network, so AnkiConnect must listen on more
than localhost: Tools → Add-ons → AnkiConnect → Config → `webBindAddress` set to
`"0.0.0.0"` (I changed this earlier; verify it if the ereader can't connect).

### Add-on `gemini_relay`

- Listens on port 8787, accepts `{"prompt": "..."}` and returns `{"text": "..."}`.
- Config (Tools → Add-ons → gemini_relay → Config): `gemini_api_key`,
  `gemini_model` (currently a Flash-Lite model), `port`.
- Logs every request with its duration to `relay.log` in the add-on folder.
- **Back up the whole `gemini_relay` folder** (copy it somewhere safe).
- Test it from PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8787/generate -Method Post -ContentType "application/json" -Body '{"prompt":"Say hello in French, JSON only."}'
```

---

## 5. Why the relay exists

Calling Gemini directly from the ereader took 9 to 120 seconds. The same request from
the PC took about 1 second. The delay was in the ereader's connection to Google, not
in the model. With the relay, the ereader only makes a short hop over the home
network. If the relay doesn't answer within 10 seconds, the plugin falls back to the
direct call.

Occasional slow calls (10 to 30 s) with the relay are usually Google being busy.
Check `relay.log`: if it shows a long time too, it was Google.

---

## 6. Every edit I made to the plugin

Search for the marker words to check which edits are still present.

| File | Change | Search for |
|---|---|---|
| `configuration.lua` | deck, note type, Gemini text provider, relay address | `relay_url`, `KOReader::AI inbox` |
| `anki_sync.lua` | always use the configured deck (no per-book deck) | `build_deck_name` should be 3 lines, no `local parent` |
| `anki_sync.lua` | tags: book title and `lang::<language>` | `lang::` |
| `anki_sync.lua` | `Translation` field sent to Anki | `["Translation"]` |
| `anki_sync.lua` | generate stubs at send time | `pending_generation` |
| `card_generator.lua` | language auto-detection, translation, no IPA or image prompt | `LANGUAGE RULE`, `"translation"` |
| `card_generator.lua` | relay call before the direct call | `relay_url` |
| `card_generator.lua` | on-screen timing (optional, diagnostic) | `AI call took` |
| `card_storage.lua` | save `translation`, `language`, `context`, `pending_generation` | `pending_generation` |
| `main.lua` | image generation switched off | `IMAGES_ENABLED` |
| `main.lua` | silent save + short popup (optional) | `QUICK_SAVE` |
| `main.lua` | save stub when offline | `OFFLINE_SAVE` |

### After a plugin update

1. **Before updating:** copy the whole plugin folder to the PC (this is the backup),
   including `configuration.lua`.
2. Update the plugin.
3. Restore `configuration.lua` from the backup if the update replaced it.
4. Search each file for the marker words above. Reapply any edit that is missing
   from section 7.
5. Restart KOReader. Test one highlight online and one with Wi-Fi off, then Send All.

---

## 7. Edit reference (the actual code)

### configuration.lua

Inside the top-level table (not inside `anki = { ... }`):

```lua
    text_provider     = "gemini",
    gemini_text_model = "gemini-3.5-flash-lite",   -- used only if the relay is unreachable
    relay_url         = "http://192.168.86.42:8787/generate",
```

Inside `anki = { ... }`:

```lua
        deck  = "KOReader::AI inbox",
        model = "KOReader AI AnkiFlashcard",
```

Note: the settings menu on the ereader saves its own values and overrides this file.

### anki_sync.lua

Replace the whole `build_deck_name` function:

```lua
local function build_deck_name(config, card)
    return (config and config.deck and config.deck ~= "")
           and config.deck or "English::Koreader"
end
```

Add one line to the `fields` table:

```lua
        ["Translation"] = card.translation or "",
```

Replace the `tags = ...` line inside the `note` table (the book-title part is optional):

```lua
        tags = (function()
            local t = {}
            for _, v in ipairs(config.tags or { "KOReader" }) do t[#t+1] = v end
            local title = card.book_title
            if title and title ~= "" then
                t[#t+1] = (title:gsub("[%s:]+", "_"))
            end
            local lang = type(card.language) == "string"
                         and (card.language:lower():gsub("[^%a]", "")) or ""
            if lang ~= "" then t[#t+1] = "lang::" .. lang end
            return t
        end)(),
```

In `AnkiSync.send_card`, right after the `if not config or not config.url ...` check
and **before** `local model = ...`:

```lua
    -- Offline stub: generate the card text now that we are sending.
    if card.pending_generation then
        if not tts_config then
            return nil, "Cannot generate offline card here"
        end
        local CardGenerator = require("card_generator")
        local CardStorage   = require("card_storage")
        local gen, gen_err = CardGenerator.generate(
            tts_config, card.phrase, card.context or "",
            card.book_title or "", card.book_author or "")
        if not gen then
            return nil, "Generation failed: " .. tostring(gen_err)
        end
        local original_phrase = card.phrase
        for _, k in ipairs({ "phrase", "language", "definition", "synonyms",
                             "translation", "text" }) do
            card[k] = gen[k] or card[k] or ""
        end
        card.pending_generation = false
        CardStorage.update_card(original_phrase, card)
    end
```

### card_generator.lua

**Prompts:** replace `PROMPT_TEMPLATE` and `TEXT_REGEN_PROMPT`:

```lua
local PROMPT_TEMPLATE = [[Flashcard for "{phrase}" from "{title}" by "{author}".
Context (for meaning only, do NOT use its words): "...{context}..."

LANGUAGE RULE: First identify the language of the highlighted phrase (use the phrase and its context). Write the definition, synonyms and example sentence in THAT SAME language. Never translate into another language, except for the translation field.

Generate a card for the highlighted phrase ONLY. Return valid JSON, no other text:
{
  "phrase": "<highlighted text in lowercase base/infinitive form, e.g. 'cranked up' → 'crank up'; use generic pronouns; never substitute a context word>",
  "language": "<the language of the phrase as one English word, e.g. French, Italian, Dutch, English>",
  "definition": "<context-aware, simple words in the phrase's language, max 20 words>",
  "synonyms": "<up to 3 common synonyms in the phrase's language, comma-separated>",
  "translation": "<1-3 Dutch equivalents of the phrase, comma-separated; empty string if the phrase is itself Dutch>",
  "text": "<sentence in the phrase's language, max 15 words, simple grammar; phrase is the only hard word; fresh scenario unrelated to the book; conjugate naturally; wrap with {{c1::...}} as it appears in the sentence, not the canonical form>"
}]]

local TEXT_REGEN_PROMPT = [[Flashcard. Phrase: "{phrase}"

LANGUAGE RULE: Identify the language of the phrase and write the sentence in THAT SAME language. Never translate.

Return valid JSON, no other text:
{
  "text": "<sentence in the phrase's language, max 15 words, simple grammar; phrase is the only hard word; fresh scenario; conjugate naturally; wrap with {{c1::...}} as it appears in the sentence, not the canonical form>",
  "image_prompt": "<vivid scene from the sentence, anime-style, widescreen 16:9, no text>"
}]]
```

**Language-neutral helpers:** replace `CardGenerator.generate_ipa` and
`CardGenerator.generate_quick_lookup` (the bottom two functions):

```lua
function CardGenerator.generate_ipa(config, phrase)
    local prompt = 'Return ONLY the pronunciation notation for the phrase: "'
                   .. (phrase or "")
                   .. '"\nFirst identify the language of the phrase, then use IPA for European '
                   .. 'languages, pinyin for Mandarin, romaji for Japanese, or the standard '
                   .. 'notation for that language.\n'
                   .. 'Reply with just the notation, nothing else. Example: /ɪɡˈzæmpəl/'

    local raw_text, err = call_llm(config, prompt)
    if not raw_text then return nil, err end
    return raw_text:match("^%s*(.-)%s*$")
end

function CardGenerator.generate_quick_lookup(config, phrase)
    local p = escape_for_prompt(phrase or "")
    local prompt = 'You are a dictionary. First identify the language of the phrase "' .. p
                .. '", then return ONLY valid JSON:\n'
                .. '{"ipa": "<pronunciation in that language: IPA for European languages, '
                .. 'pinyin for Mandarin, romaji for Japanese>", '
                .. '"definition": "<simple, clear definition in that SAME language, max 15 words>"}'

    local raw_text, err = call_llm(config, prompt)
    if not raw_text then return nil, err end
    local result = parse_response(raw_text)
    if result and result.ipa and result.definition then
        return result
    end
    return nil, "Unexpected API response"
end
```

**Relay call:** in `call_llm`, directly after `local response_body = {}`:

```lua
    if config.relay_url and config.relay_url ~= "" then
        local rb   = {}
        local body = json.encode({ prompt = prompt })
        http.TIMEOUT = 10
        local _, code = http.request {
            url     = config.relay_url,
            method  = "POST",
            headers = {
                ["Content-Type"]   = "application/json",
                ["Content-Length"] = tostring(#body),
            },
            source = ltn12.source.string(body),
            sink   = ltn12.sink.table(rb),
        }
        if tostring(code) == "200" then
            local ok, data = pcall(json.decode, table.concat(rb))
            if ok and type(data) == "table" and type(data.text) == "string" then
                return data.text
            end
        end
    end
```

**Timing popup (optional):** the last lines of `CardGenerator.generate`:

```lua
    local socket = require("socket")
    local t0 = socket.gettime()
    local raw_text, err = call_llm(config, prompt)
    local secs = socket.gettime() - t0
    local UIManager    = require("ui/uimanager")
    local Notification = require("ui/widget/notification")
    UIManager:show(Notification:new {
        text    = string.format("AI call took %.1f s", secs),
        timeout = 5,
    })
    if not raw_text then return nil, err end
    return parse_response(raw_text)
end
```

### card_storage.lua

In `CardStorage.save_card`, after `text = card.text or "",`:

```lua
        translation        = card.translation        or "",
        language           = card.language           or "",
        context            = card.context            or "",
        pending_generation = card.pending_generation or false,
```

In `CardStorage.update_card`, after `e.synonyms = ...`:

```lua
            e.translation  = new_card.translation or e.translation or ""
            e.language     = new_card.language    or e.language    or ""
```

and after `e.updated_at = os.time()`:

```lua
            e.pending_generation = false
```

### main.lua

Near the top, under `local MAX_TITLE`:

```lua
local IMAGES_ENABLED = false   -- true = generate illustrations again
local QUICK_SAVE     = true    -- optional: save silently + short popup
local OFFLINE_SAVE   = true    -- save a stub when there is no connection
```

In `can_generate_image`, first line of the function:

```lua
    if not IMAGES_ENABLED then return false end
```

In `on_regenerate` change `if new_card.image_prompt then` to:

```lua
                                    if IMAGES_ENABLED and new_card.image_prompt then
```

In `on_regen_text` change `if new_prompt then` to:

```lua
                                        if IMAGES_ENABLED and new_prompt then
```

In the "Anki Card" callback, right after the first `ui.highlight:onClose()`:

```lua
                if OFFLINE_SAVE and not NetworkMgr:isOnline() then
                    local ok_s, save_err = CardStorage.save_card({
                        phrase             = phrase,
                        context            = context,
                        book_title         = title,
                        book_author        = author,
                        highlight_pos0     = highlight_pos0,
                        highlight_pos1     = highlight_pos1,
                        pending_generation = true,
                    })
                    UIManager:show(Notification:new {
                        text = (ok_s or save_err == "already_saved")
                               and (_("Saved for later: ") .. phrase)
                               or _("Could not save card"),
                        timeout = 3,
                    })
                    return
                end
```

In `do_generate`, directly after `card.highlight_pos1 = highlight_pos1` (the first
occurrence, not the ones inside `on_regenerate`):

```lua
                    if QUICK_SAVE then
                        local ok_s, save_err = CardStorage.save_card(card)
                        local msg = capitalize_first(card.phrase or phrase)
                        if card.definition and card.definition ~= "" then
                            msg = msg .. ": " .. card.definition
                        end
                        if card.translation and card.translation ~= "" then
                            msg = msg .. "\n→ " .. card.translation
                        end
                        if not ok_s and save_err ~= "already_saved" then
                            msg = msg .. "\n(" .. _("could not save card") .. ")"
                        end
                        UIManager:show(InfoMessage:new { text = msg, timeout = 6 })
                        return
                    end
```

---

## 8. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| "Deck not found: KOReader::SomeBook" | The `build_deck_name` edit is gone (per-book decks are back), or the configured deck doesn't exist in Anki |
| "One or more notes failed validation" | Note type mismatch: wrong `model` name, missing or misspelled field, `Phrase` not first. Ask AnkiConnect for the exact reason (below) |
| Anki popup "WinError 10022 / invalid argument" | Known AnkiConnect socket bug on Windows. Harmless if cards still arrive: click Close |
| Card takes 10+ s | Relay not running (Anki closed?). Check `relay.log` for fresh lines |
| Anki says "could not start on port 8787" | Another program uses the port (for example the old PowerShell relay script). Stop it |
| No translation or `lang::` tag on a card | `card_storage.lua` edit lost, or the `Translation` field is missing in the note type. Old cards never get them |
| "Card generation failed: HTTP 503" | Google is overloaded. Try again |
| Changing `configuration.lua` has no effect | Device settings override it: Anki Manage → Anki Settings, or delete `anki_flashcards_settings.json` |
| Ereader freezes for a long time on a Wi-Fi network that isn't home | The plugin waits for timeouts while trying to reach the PC. Until the fix in section 9.1 is applied, turn off auto-send on Wi-Fi in Anki Settings and send cards at home |
| API key leaked | Delete it in Google AI Studio, create a new one, update the add-on config (and `gemini_api_key` in `configuration.lua` if used) |

Ask AnkiConnect why a note would be rejected (PowerShell, Anki open):

```powershell
$body = @{
  action  = "canAddNotesWithErrorDetail"
  version = 6
  params  = @{ notes = @(@{
    deckName  = "KOReader::AI inbox"
    modelName = "KOReader AI AnkiFlashcard"
    fields    = @{
      Phrase = "test"; IPA = "test"; Definition = "test"; Synonyms = "test"
      Text   = "Dit is een {{c1::test}} zin"; Source = "test"; Translation = "test"
    }
    tags = @("KOReader")
  }) }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri http://localhost:8765 -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
```

---

## 9. Ideas for later

- **Freezes on other Wi-Fi networks:** the ereader can hang for a long time on a
  network that isn't home. Cause and a proposed fix are in section 9.1 (not yet applied).
- **Git:** fork the plugin on GitHub so the edits become commits and updates can be
  merged instead of redone by hand.
- **Own dictionary:** build a StarDict dictionary from kaikki.org Wiktionary data,
  with inflected forms in a `.syn` file. Decide first: definitions in the word's own
  language, or in one language (Dutch/English).
- **Source field:** as far as I can tell it is always empty. `main.lua` builds a
  "Title — Author" string but never uses it.
- **Direct fallback:** only retries on HTTP 429, not 503.
- **Anki add-on that creates the note itself:** the ereader would send only the
  highlight and context; the add-on would generate the card and add it directly.

### 9.1 Freezes on other Wi-Fi networks (proposed fix, not yet applied)

Written but **not tested yet**. Test it before relying on it (see the test plan below).

**Problem.** On a Wi-Fi network other than home, the ereader can freeze for a long time.
KOReader counts itself as "online" as soon as it has any connection, so the plugin
behaves as if it were at home and tries to reach the PC at `192.168.86.42`, which
doesn't exist on that network. All of this runs on the main thread, so the whole screen
stops while the plugin waits for timeouts:

- **Highlight → Anki Card:** waits up to 10 s for the relay, then falls back to the
  direct Gemini call (9 to 120 s).
- **Auto-send (if switched on in Anki Settings):** every 60 seconds it tries each unsent
  card against AnkiConnect (5 s timeout per card). For offline stubs it first tries to
  generate the text (relay timeout plus the slow direct call) before the send itself
  fails. Several unsent cards can freeze the ereader for minutes, with no highlight made.
- **Send All Unsent:** the same, once per card.

**Which one is it?** Freezing while you are just reading (no highlight) points to
auto-send. Freezing right after tapping Anki Card points to generation.

**Workaround until fixed.** Turn off auto-send on Wi-Fi in Anki Settings (the code
reads an `auto_send_wifi` setting) and send cards manually at home.

**Fix idea.** Before doing anything that involves the PC, run a quick check: a TCP
connection attempt to the PC with a 1.5 s timeout, remembered for 30 s. If the PC is
not reachable:

- Highlight → Anki Card saves a stub immediately (like offline mode), with no waiting.
- The auto-send tick skips silently.
- Send All stops at once with "PC not reachable".
- The relay is skipped instead of waited for.

Consequences:

- Anki closed at home counts as "away": you get "Saved for later" instead of a card.
- On another network with working internet you also get a stub instead of a card popup.
  The planned Wiktionary dictionary would cover the "what does this word mean" need.
- Purple quick-lookup highlights still use the direct call on other networks, but they
  no longer wait for the relay first.
- Use an IP address (not a host name) in `anki.url` and `relay_url`, because a DNS
  lookup is not covered by the short timeout.

**Edits.** One new file and four small edits. Remember `git add` for the new file.

1. New file `AnkiFlashcards.koplugin/pc_reach.lua`:

```lua
-- Quick "can I reach my PC?" check with a short timeout, cached per host:port.
local socket = require("socket")

local PcReach = {}
local cache = {}
local CACHE_SECS = 30
local TIMEOUT    = 1.5

local function parse(url)
    local host, port = (url or ""):match("^https?://([^/:]+):?(%d*)")
    if not host then return nil end
    return host, tonumber(port) or 80
end

function PcReach.pc_up(url)
    local host, port = parse(url)
    if not host then return false end
    local key = host .. ":" .. port
    local now = socket.gettime()
    local hit = cache[key]
    if hit and now - hit.at < CACHE_SECS then return hit.ok end
    local tcp = socket.tcp()
    tcp:settimeout(TIMEOUT)
    local ok = tcp:connect(host, port) and true or false
    tcp:close()
    cache[key] = { ok = ok, at = now }
    return ok
end

return PcReach
```

2. `card_generator.lua`: add near the other `require` lines at the top:

```lua
local PcReach = require("pc_reach")
```

and change the relay condition in `call_llm` to:

```lua
    if config.relay_url and config.relay_url ~= "" and PcReach.pc_up(config.relay_url) then
```

3. `anki_sync.lua`: in `AnkiSync.send_card`, after the `if not config or not config.url ...`
check and **before** the offline stub block:

```lua
    local PcReach = require("pc_reach")
    if not PcReach.pc_up(config.url) then
        return nil, "PC not reachable (not on your home network, or Anki is closed)"
    end
```

4. `main.lua`, three changes:

   a. Near the other `require` lines at the top:

```lua
local PcReach = require("pc_reach")
```

   b. In the "Anki Card" callback, change the offline check to:

```lua
                if OFFLINE_SAVE and (not NetworkMgr:isOnline()
                        or not PcReach.pc_up(get_anki_config().url)) then
```

   c. In `auto_send_tick`, after `if not NetworkMgr:isOnline() then return end`:

```lua
        if not PcReach.pc_up(cfg.url) then return end
```

**Marker to search for once applied:** `pc_reach` (in `card_generator.lua`,
`anki_sync.lua`, `main.lua`, plus the new file).

**Test plan.** Use a phone hotspot as the "other network".

1. At home, Anki open: highlight a word. You should get the normal card popup.
2. At home, Anki closed: you should get "Saved for later". Open Anki and use
   Send All Unsent: the text is generated and the cards arrive.
3. On the hotspot: highlight a word. "Saved for later" should appear within about two
   seconds, with no freeze. Leave the ereader reading for a few minutes with unsent
   cards: no freezes from auto-send.
4. Back home: Send All Unsent should work again.
