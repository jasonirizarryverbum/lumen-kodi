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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lumen_art import write_logo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "src" / "skin.lumen"
VERSION = "0.9.7"
TMDBH = "plugin://plugin.video.themoviedb.helper/?info={info}&amp;tmdb_type={kind}&amp;widget=true&amp;nextpage=false"

ADDON_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="skin.lumen" version="{VERSION}" name="Lumen" provider-name="Lumen (based on Estuary by phil65, Ichabod Fletchman)">
	<requires>
		<import addon="xbmc.gui" version="5.17.0"/>
		<import addon="script.lumen.setup" version="0.9.7"/>
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
    # Trakt rows stay hidden until Lumen Setup sees a Trakt sign-in; otherwise
    # TMDb Helper raises a "401 unauthorised" dialog every time home opens.
    conds = []
    if info.startswith("trakt_"):
        conds.append("Skin.HasSetting(lumen_trakt)")
    if not lite_ok:
        conds.append("!Skin.HasSetting(lumen_lite)")
    cond = f' condition="{" + ".join(conds)}"' if conds else ""
    if kind_include == "WidgetListPoster":
        # Clicking a poster opens the details page (plot, cast, trailer, play)
        # instead of starting playback straight away.
        extra += (
            '\t\t\t\t\t\t\t<param name="onclick_condition" value="true"/>\n'
            '\t\t\t\t\t\t\t<param name="onclick_action" value="Action(Info)"/>\n'
        )
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


def _touch_button(suffix, top, action, flip):
    return f"""
			<control type="button" id="$PARAM[scrollbar_id]{suffix}">
				<left>0</left>
				<top>{top}</top>
				<width>110</width>
				<height>110</height>
				<texturefocus colordiffuse="button_focus">colors/white.png</texturefocus>
				<texturenofocus colordiffuse="DD1A1E2B">colors/white.png</texturenofocus>
				<onclick>{action}($PARAM[scrollbar_id])</onclick>
			</control>
			<control type="image">
				<left>31</left>
				<top>{top + 31}</top>
				<width>48</width>
				<height>48</height>
				<aspectratio>keep</aspectratio>
				<texture flipy="{flip}">overlays/arrowdown.png</texture>
			</control>"""


TOUCH_ARROWS = (
    """
		<control type="group">
			<right>40</right>
			<bottom>60</bottom>
			<width>110</width>
			<height>370</height>
			<control type="button" id="$PARAM[scrollbar_id]3">
				<description>Brings the auto-hidden side menu back on touch screens</description>
				<left>0</left>
				<top>0</top>
				<width>110</width>
				<height>110</height>
				<align>center</align>
				<aligny>center</aligny>
				<textoffsetx>0</textoffsetx>
				<font>font12</font>
				<label>MENU</label>
				<texturefocus colordiffuse="button_focus">colors/white.png</texturefocus>
				<texturenofocus colordiffuse="DD1A1E2B">colors/white.png</texturenofocus>
				<onclick>SetProperty(lumen_menu,1,home)</onclick>
				<onunfocus>ClearProperty(lumen_menu,home)</onunfocus>
				<visible>!Skin.HasSetting(lumen_keep_menu)</visible>
			</control>"""
    + _touch_button(1, 130, "PageUp", "true")
    + _touch_button(2, 260, "PageDown", "false")
    + """
		</control>"""
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
    # Once per Kodi session, let Lumen Setup re-check whether the Trakt rows can be shown.
    onloads += '\t<onload condition="String.IsEmpty(Window(home).Property(lumen_synced))">RunScript(script.lumen.setup,sync)</onload>\n'
    onloads += "\t<onload>SetProperty(lumen_synced,1,home)</onload>\n"
    text = sub_once(r"(<defaultcontrol>9000</defaultcontrol>\n)", lambda m: m.group(1) + onloads, text)

    # 5. Auto-hide the side menu while the rows have focus, and let the rows use
    #    the space. Lumen Setup can turn this off (lumen_keep_menu).
    # lumen_menu is set by the touch MENU button: a tapped button keeps focus,
    # so on touch screens focus alone cannot bring the menu back.
    hide = ("ControlGroup(2000).HasFocus + !Skin.HasSetting(lumen_keep_menu)"
            " + String.IsEmpty(Window(home).Property(lumen_menu))")

    def slide(distance, tabs):
        return (
            f'{tabs}<animation effect="slide" end="-{distance},0" time="300" tween="cubic" '
            f'easing="out" condition="{hide}">Conditional</animation>\n'
        )

    text = sub_once(
        r'(<control type="group" id="2000">\s*<left>462</left>\n)',
        # Rows are only widened when the menu auto-hides; with the menu pinned
        # (touch screens) they keep the stock width so nothing sits off-screen.
        lambda m: m.group(1)
        + '\t\t\t\t<include condition="!Skin.HasSetting(lumen_keep_menu)">LumenWideRows</include>\n'
        + slide(400, "\t\t\t\t"),
        text,
    )
    text = sub_once(
        r"(<depth>DepthContentPanel</depth>\s*<include>OpenClose_Left</include>\n)",
        lambda m: m.group(1) + slide(522, "\t\t\t\t"),
        text,
    )

    # 6. Lumen mark and wordmark in place of the Kodi logo; it hides with the menu.
    t = "\t\t\t\t"
    logo = (
        slide(522, t)
        + f"{t}<control type=\"image\">\n{t}\t<left>0</left>\n{t}\t<top>-2</top>\n"
        f"{t}\t<width>60</width>\n{t}\t<height>60</height>\n{t}\t<aspectratio>keep</aspectratio>\n"
        f"{t}\t<texture>lumen-logo.png</texture>\n{t}</control>\n"
        f"{t}<control type=\"label\">\n{t}\t<left>80</left>\n{t}\t<top>-2</top>\n"
        f"{t}\t<width>300</width>\n{t}\t<height>60</height>\n{t}\t<aligny>center</aligny>\n"
        f"{t}\t<font>font37</font>\n{t}\t<textcolor>white</textcolor>\n"
        f"{t}\t<label>LUMEN</label>\n{t}</control>\n"
    )
    text = sub_once(
        r'[ \t]*<control type="image">\s*<left>4</left>\s*<top>0</top>\s*<aspectratio>keep</aspectratio>\s*'
        r"<width>192</width>\s*<height>56</height>\s*<texture>special://xbmc/media/vendor_logo\.png</texture>\s*</control>\n",
        lambda m: logo,
        text,
    )
    return text


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    src = Path(sys.argv[1])
    if not (src / "xml" / "Home.xml").is_file():
        raise SystemExit(f"{src} does not look like skin.estuary")

    icon = DEST / "resources" / "icon.png"
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
    inc = DEST / "xml" / "Includes_Home.xml"
    inc_text = sub_once(
        r"</includes>\s*$",
        '\t<include name="LumenWideRows">\n\t\t<width>1858</width>\n\t</include>\n</includes>\n',
        inc.read_text(encoding="utf-8"),
    )
    # Touch mode: big up/down buttons beside the scrollbar, because a vertical
    # swipe that starts on a poster row is swallowed by that row.
    inc_text = sub_once(
        r'(<include name="WidgetScrollbar">.*?)(\n\t</include>)',
        lambda m: m.group(1) + TOUCH_ARROWS + m.group(2),
        inc_text,
        flags=re.S,
    )
    inc.write_text(inc_text, encoding="utf-8", newline="\n")
    icon.unlink(missing_ok=True)  # build_repo.py draws the Lumen icon
    write_logo(DEST / "media" / "lumen-logo.png")
    print(f"wrote {DEST}")


if __name__ == "__main__":
    main()
