"""Regenerate src/skin.lumen from a stock Estuary checkout.

Usage:  python -I tools/fork_estuary.py <path-to-xbmc>/addons/skin.estuary

Estuary is (c) phil65 / Team Kodi, CC BY-SA 4.0 + GPL-2.0. Lumen keeps the
same licence. Every change Lumen makes to Estuary lives in this file, so the
fork can be redone against a newer Estuary (e.g. for Kodi 22).
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "src" / "skin.lumen"
VERSION = "0.9.0"
TMDBH = "plugin://plugin.video.themoviedb.helper/?info={info}&amp;tmdb_type={kind}&amp;widget=true&amp;nextpage=false"

ADDON_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="skin.lumen" version="{VERSION}" name="Lumen" provider-name="Lumen (based on Estuary by phil65, Ichabod Fletchman)">
	<requires>
		<import addon="xbmc.gui" version="5.17.0"/>
		<import addon="script.lumen.setup" version="0.9.0"/>
	</requires>
	<extension point="xbmc.gui.skin" debugging="false">
		<res width="1920" height="1440" aspect="4:3" default="false" folder="xml" />
		<res width="1920" height="1280" aspect="3:2" default="false" folder="xml" />
		<res width="1920" height="1200" aspect="16:10" default="false" folder="xml" />
		<res width="2040" height="1080" aspect="17:9" default="false" folder="xml" />
		<res width="1920" height="1080" aspect="16:9" default="true" folder="xml" />
		<res width="2560" height="1080" aspect="21:9" default="false" folder="xml" />
		<res width="2338" height="1080" aspect="19.5:9" default="false" folder="xml" />
		<res width="2160" height="1080" aspect="18:9" default="false" folder="xml" />
	</extension>
	<extension point="xbmc.addon.metadata">
		<platform>all</platform>
		<license>CC BY-SA 4.0, GNU GENERAL PUBLIC LICENSE Version 2.0</license>
		<source>https://github.com/jasonirizarryverbum/lumen-kodi</source>
		<assets>
			<icon>resources/icon.png</icon>
		</assets>
		<summary lang="en_GB">Lumen: a dark, lightweight, streaming-first skin.</summary>
		<description lang="en_GB">Lumen is a lean fork of Estuary (by phil65 and Team Kodi) with a dark palette and a home screen driven by Trakt and TMDb rows, plus local library rows for NAS content. Built for low-memory Google TV devices.</description>
	</extension>
</addon>
"""

COLORS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<colors>
	<color name="primary_background">FF1A1E2B</color>
	<color name="secondary_background">33E8505B</color>
	<color name="dialog_tint">FF11141B</color>
	<color name="background">FF07080B</color>
	<color name="bg_image">FF909090</color>
	<color name="bg_overlay">24FFFFFF</color>
	<color name="black">FF000000</color>
	<color name="white">FFF2F2F4</color>
	<color name="grey">FF9AA0AD</color>
	<color name="blue">FFFFB4A8</color>
	<color name="red">FFCE4421</color>
	<color name="button_focus">FFE8505B</color>
	<color name="button_alt_focus">80E8505B</color>
	<color name="text_shadow">22000000</color>
	<color name="border_alpha">40FFFFFF</color>
	<color name="disabled">40FFFFFF</color>
	<color name="selected">FFFFC857</color>
	<color name="invalid">FFFF0000</color>
</colors>
"""

# Home menu entries hidden on first run (re-enable under Skin settings > Main menu items).
HIDDEN_MENU = ["Music", "MusicVideo", "TV", "Radio", "Games", "Pictures", "Weather"]


def row(kind_include, list_id, header, info, kind, lite_ok=True, extra=""):
    cond = "" if lite_ok else ' condition="!Skin.HasSetting(lumen_lite)"'
    return (
        f'\t\t\t\t\t\t<include content="{kind_include}"{cond}>\n'
        f'\t\t\t\t\t\t\t<param name="content_path" value="{TMDBH.format(info=info, kind=kind)}"/>\n'
        f'\t\t\t\t\t\t\t<param name="widget_header" value="{header}"/>\n'
        f'\t\t\t\t\t\t\t<param name="widget_target" value="videos"/>\n'
        f'\t\t\t\t\t\t\t<param name="list_id" value="{list_id}"/>\n'
        f"{extra}"
        f"\t\t\t\t\t\t</include>\n"
    )


MOVIE_ROWS = (
    row("WidgetListPoster", 5020, "Watchlist", "trakt_watchlist", "movie")
    + row("WidgetListPoster", 5030, "Trending this week", "trending_week", "movie")
    + row("WidgetListPoster", 5040, "Popular", "popular", "movie")
    + row("WidgetListPoster", 5050, "In cinemas", "now_playing", "movie", lite_ok=False)
    + row("WidgetListPoster", 5060, "Coming soon", "upcoming", "movie", lite_ok=False)
)
TV_ROWS = (
    row("WidgetListEpisodes", 6020, "Up next", "trakt_nextepisodes", "tv")
    + row("WidgetListPoster", 6030, "Watchlist", "trakt_watchlist", "tv")
    + row("WidgetListPoster", 6040, "Trending this week", "trending_week", "tv")
    + row("WidgetListPoster", 6050, "Popular", "popular", "tv", lite_ok=False)
    + row("WidgetListPoster", 6060, "Airing today", "airing_today", "tv", lite_ok=False)
)


def sub_once(pattern, repl, text, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"patch did not apply: {pattern!r}")
    return new


def patch_home(text):
    # 1. Streaming rows at the top of the Movies and TV shows sections.
    for group, pager, rows in ((5001, 5010, MOVIE_ROWS), (6001, 6010, TV_ROWS)):
        anchor = (
            rf'(<control type="grouplist" id="{group}">\s*'
            rf"<include>WidgetGroupListCommon</include>\s*"
            rf"<pagecontrol>{pager}</pagecontrol>\n)"
        )
        text = sub_once(anchor, lambda m, r=rows: m.group(1) + r, text)

    # 2. Drop the "your library is empty" panels: those sections now always have rows.
    for media in ("movies", "tvshows"):
        text = sub_once(
            rf'[ \t]*<include content="ImageWidget" condition="!Library\.HasContent\({media}\)">.*?</include>\n',
            "",
            text,
            flags=re.S,
        )

    # 3. Lite mode: no full-screen fanart behind the home screen.
    text = sub_once(
        r"(\$VAR\[HomeFanartVar\]</imagepath>\s*<visible>)!Player\.HasMedia(</visible>)",
        r"\1!Player.HasMedia + !Skin.HasSetting(lumen_lite)\2",
        text,
    )

    # 4. First-run defaults: trim the main menu and open the setup wizard once.
    first = '!Skin.HasSetting(lumen_firstrun)'
    onloads = "".join(
        f'\t<onload condition="{first}">Skin.SetBool(HomeMenuNo{name}Button)</onload>\n'
        for name in HIDDEN_MENU
    )
    onloads += f'\t<onload condition="{first}">RunScript(script.lumen.setup,firstrun)</onload>\n'
    onloads += f'\t<onload condition="{first}">Skin.SetBool(lumen_firstrun)</onload>\n'
    text = sub_once(r"(<defaultcontrol>9000</defaultcontrol>\n)", lambda m: m.group(1) + onloads, text)
    return text


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    src = Path(sys.argv[1])
    if not (src / "xml" / "Home.xml").is_file():
        raise SystemExit(f"{src} does not look like skin.estuary")

    icon = DEST / "resources" / "icon.png"
    keep_icon = icon.read_bytes() if icon.is_file() else None
    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(src, DEST)

    # Themes need compiled .xbt files and the screenshots show Estuary, not Lumen.
    shutil.rmtree(DEST / "themes", ignore_errors=True)
    for shot in (DEST / "resources").glob("screenshot-*.jpg"):
        shot.unlink()
    (DEST / "resources" / "fanart.jpg").unlink(missing_ok=True)
    for color in (DEST / "colors").glob("*.xml"):
        color.unlink()

    (DEST / "addon.xml").write_text(ADDON_XML, encoding="utf-8", newline="\n")
    (DEST / "colors" / "defaults.xml").write_text(COLORS_XML, encoding="utf-8", newline="\n")
    home = DEST / "xml" / "Home.xml"
    home.write_text(patch_home(home.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    if keep_icon:
        icon.write_bytes(keep_icon)
    else:
        icon.unlink(missing_ok=True)  # build_repo.py draws the Lumen icon
    print(f"wrote {DEST}")


if __name__ == "__main__":
    main()
