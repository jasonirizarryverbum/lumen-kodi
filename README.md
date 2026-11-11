# Lumen for Kodi

A dark, lightweight, streaming-first Kodi setup for low-memory Google TV devices
(Chromecast with Google TV, projectors). Targets **Kodi 21 "Omega"**.

It is three small add-ons, not a "build" that overwrites your Kodi:

| Add-on | What it does |
|---|---|
| `skin.lumen` | Fork of Kodi's Estuary skin: dark palette, trimmed main menu, Trakt/TMDb rows on the Movies and TV shows screens, local library rows underneath once a library exists |
| `script.lumen.setup` | Setup tool: performance profile, Trakt sign-in, default player, NAS share |
| `repository.lumen` | Delivers updates for the two above |

Discovery and tracking come from [TMDb Helper](https://kodi.wiki/view/Add-on:TheMovieDb_Helper),
installed automatically. The Lumen repository passes through TMDb Helper's own
repository so you get version 6, because the 5.x in the official Kodi repository
throws errors on Kodi 21. Lumen ships no streaming add-ons: playback goes to whichever TMDb Helper player you install yourself.

## Install

1. Kodi > Settings > System > Add-ons > turn on **Unknown sources**.
2. Settings > File manager > **Add source** > `https://jasonirizarryverbum.github.io/lumen-kodi/` > name it `lumen`.
3. Settings > Add-ons > **Install from zip file** > `lumen` > `repository.lumen-1.0.2.zip`.
4. **Install from repository** > Lumen Repository > Look and feel > Skin > **Lumen** > Install, and accept the switch.
5. The setup tool opens the first time the Lumen home screen loads. Pick the device profile, then restart Kodi.

## Profiles

| | Chromecast / 2 GB (Lite) | Projector / 4 GB (Full) |
|---|---|---|
| Rows per screen | 3 | 5 |
| Fanart behind the home screen | off | on |
| Cached poster / fanart size | 540 / 720 px | 720 / 1080 px |
| Video cache | 48 MB | 96 MB |

Artwork sizes are written to `advancedsettings.xml` (the original is kept as
`advancedsettings.xml.lumen-backup`).

## Developing

```
python -I tools/fork_estuary.py <xbmc checkout>/addons/skin.estuary   # regenerate src/skin.lumen
python -I tools/build_repo.py                                          # rebuild docs/ (GitHub Pages)
```

Every change Lumen makes to Estuary is in `tools/fork_estuary.py`. To publish an
update, raise the version in the add-on's `addon.xml` (and `VERSION` in
`fork_estuary.py` for the skin), rebuild, commit and push.

## Credits and licence

The skin is derived from Estuary by phil65 and Team Kodi and stays under
CC BY-SA 4.0 / GPL-2.0 (see `src/skin.lumen/LICENSE.txt`). The tools and setup
script are GPL-2.0-or-later.
