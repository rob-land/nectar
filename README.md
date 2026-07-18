# Nectar (`land.rob.Nectar`)

Seven letters, one hive, one puzzle a day. The Spelling-Bee-shaped word
game, native for GNOME and Phosh — because running an entire Android
container to play a word puzzle is a war crime against RAM.

Usual `land.rob.*` construction: GTK4 + libadwaita + PyGObject, meson,
SQLite, Flatpak. **No network permission at all** — the dictionary is
bundled and puzzles are generated on-device.

## How it works

- **Daily + deterministic**: the puzzle is seeded from the date
  (SHA-256 of `nectar:YYYY-MM-DD`), so every device shows the same hive
  on the same day with zero server involvement.
- **Generation**: a pangram base word is drawn from a curated list of
  ~1,400 common 7-distinct-letter words; a center letter is chosen so
  the answer count lands between 20 and 75. Answers are computed
  against a ~188k-word dictionary. Takes ~2 s, runs once per day on a
  background thread behind a loading page, then is cached in SQLite.
- **Scoring**: 4-letter words are 1 pt, longer words are their length,
  pangrams +7. Ranks from Larva to Queen Bee.
- **Progress** persists per-day (SQLite), so closing the app mid-hive
  loses nothing.
- **Input**: tap the honeycomb on the phone, or just type on the
  desktop — letters, Backspace, Enter all work.

## Word lists

- `data/wordlists/valid.txt` — accepted guesses; filtered from
  dwyl/english-words (4+ letters, ≤7 distinct).
- `data/wordlists/pangrams.txt` — puzzle bases; common words with
  exactly 7 distinct letters, intersected with the valid list.

Yes, the big list accepts some deeply obscure words. That's the fun
kind of forgiving. Swap in a stricter SCOWL cut if it bothers you.

## Building

```sh
GSETTINGS_SCHEMA_DIR=data/ python3 -m src.main   # dev run
flatpak-builder --user --install --force-clean build land.rob.Nectar.json
```

## Obvious next steps

- App icon (a hex, obviously)
- Stats page (streak, average rank) — the tables are already there
- Yesterday's answers reveal
- A two-player same-hive race over XMPP, if you ever want Patch's
  stack to earn its keep in a game
