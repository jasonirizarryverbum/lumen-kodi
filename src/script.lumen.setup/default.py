"""Lumen Setup: performance profile, Trakt, default player and NAS share."""
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

NAME = "Lumen Setup"
SKIN_ID = "skin.lumen"
TMDBH = "plugin.video.themoviedb.helper"

# label, lite skin mode, poster px, fanart px, video cache MB, touch screen
PROFILES = [
    ("Chromecast / 2 GB devices (Lite)", True, 540, 720, 48, False),
    ("Projector / 4 GB devices (Full)", False, 720, 1080, 96, False),
    ("Phone or tablet (touch screen)", False, 720, 1080, 96, True),
]

dialog = xbmcgui.Dialog()


def rpc(method, **params):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        return json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    except Exception:
        return {"error": "bad response"}


def userdata(name):
    return xbmcvfs.translatePath("special://profile/" + name)


def load_xml(path, root_tag):
    """Return the parsed file, or a fresh root. None means the file is unreadable."""
    if not os.path.isfile(path):
        return ET.Element(root_tag)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    return root if root.tag == root_tag else None


def save_xml(path, root):
    backup = path + ".lumen-backup"
    if os.path.isfile(path) and not os.path.isfile(backup):
        shutil.copyfile(path, backup)
    if hasattr(ET, "indent"):
        ET.indent(root, space="    ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def set_child(parent, tag, value):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = str(value)


def has_addon(addon_id):
    return xbmc.getCondVisibility("System.AddonIsEnabled(%s)" % addon_id)


def apply_profile():
    choice = dialog.select("Which device is this?", [p[0] for p in PROFILES])
    if choice < 0:
        return False
    label, lite, imageres, fanartres, cache_mb, touch = PROFILES[choice]

    notes = []
    path = userdata("advancedsettings.xml")
    root = load_xml(path, "advancedsettings")
    if root is None:
        notes.append("advancedsettings.xml could not be read, so artwork sizes were left alone.")
    else:
        set_child(root, "imageres", imageres)
        set_child(root, "fanartres", fanartres)
        save_xml(path, root)

    result = rpc("Settings.SetSettingValue", setting="filecache.memorysize", value=cache_mb)
    if "error" in result:
        notes.append("The video cache size could not be set here. Set it under Settings > Services > Caching.")

    if xbmc.getSkinDir() == SKIN_ID:
        xbmc.executebuiltin("Skin.SetBool(lumen_lite)" if lite else "Skin.Reset(lumen_lite)")
        # Touch screens get the skin's touch mode (scrollbars, back button) and a
        # pinned menu, because there is no "left" key to bring a hidden menu back.
        for setting in ("touchmode", "lumen_keep_menu"):
            xbmc.executebuiltin(("Skin.SetBool(%s)" if touch else "Skin.Reset(%s)") % setting)
        xbmc.executebuiltin("ReloadSkin()")
    else:
        notes.append("Switch to the Lumen skin and run this again to apply the home screen part.")

    message = "Applied: %s.[CR]Restart Kodi for the artwork sizes to take effect." % label
    if notes:
        message += "[CR][CR]" + "[CR]".join(notes)
    dialog.ok(NAME, message)
    return True


def need_tmdbh():
    if has_addon(TMDBH):
        return True
    dialog.ok(NAME, "TMDb Helper is not installed or is disabled. Install it from the Kodi add-on repository first.")
    return False


def trakt_connected():
    try:
        return bool(xbmcaddon.Addon(TMDBH).getSetting("trakt_token"))
    except Exception:
        return False


def trakt_rows_work():
    """TMDb Helper 5.x (Kodi's official repo) crashes building Trakt rows on
    Kodi 21.3, popping an error on every home visit. Only 6.x and later work."""
    try:
        major = int(xbmcaddon.Addon(TMDBH).getAddonInfo("version").split(".")[0])
    except Exception:
        return False
    return major >= 6


def sync_trakt_rows():
    """Show the Trakt home rows only while TMDb Helper holds a Trakt sign-in."""
    if xbmc.getSkinDir() != SKIN_ID:
        return
    want = trakt_connected() and trakt_rows_work()
    have = bool(xbmc.getCondVisibility("Skin.HasSetting(lumen_trakt)"))
    if want != have:
        xbmc.executebuiltin("Skin.SetBool(lumen_trakt)" if want else "Skin.Reset(lumen_trakt)")
        xbmc.executebuiltin("ReloadSkin()")


def connect_trakt():
    if not need_tmdbh():
        return
    if trakt_connected():
        sync_trakt_rows()
        dialog.ok(NAME, "Trakt is already connected. The Watchlist and Up next rows are on.")
        return
    xbmc.executebuiltin("RunScript(%s,authenticate_trakt)" % TMDBH)
    monitor = xbmc.Monitor()
    for _ in range(100):  # wait up to five minutes for the sign-in to finish
        if monitor.waitForAbort(3):
            return
        if trakt_connected():
            sync_trakt_rows()
            return


def choose_player(kind):
    if not need_tmdbh():
        return
    dialog.ok(
        NAME,
        "TMDb Helper will list the players it knows about. A player is offered once the "
        "add-on it belongs to is installed, so install your playback add-on first.",
    )
    xbmc.executebuiltin("RunScript(%s,set_defaultplayer=%s)" % (TMDBH, kind))


def add_nas():
    schemes = [("SMB (Windows / most NAS boxes)", "smb"), ("NFS", "nfs")]
    choice = dialog.select("How does the NAS share its files?", [s[0] for s in schemes])
    if choice < 0:
        return
    scheme = schemes[choice][1]
    host = dialog.input("NAS address (name or IP)").strip().strip("/")
    if not host:
        return
    share = dialog.input("Share and folder, for example media/Movies").strip().strip("/")
    if not share:
        return
    label = dialog.input("Name to show in Kodi", "NAS").strip() or "NAS"
    url = "%s://%s/%s/" % (scheme, host, share)

    path = userdata("sources.xml")
    root = load_xml(path, "sources")
    if root is None:
        dialog.ok(NAME, "sources.xml could not be read, so nothing was changed. Add the share from Videos > Files > Add videos instead.")
        return
    video = root.find("video")
    if video is None:
        video = ET.SubElement(root, "video")
        ET.SubElement(video, "default", pathversion="1")
    for source in video.findall("source"):
        if (source.findtext("path") or "").rstrip("/") == url.rstrip("/"):
            dialog.ok(NAME, "%s is already a video source." % url)
            return
    source = ET.SubElement(video, "source")
    ET.SubElement(source, "name").text = label
    ET.SubElement(source, "path", pathversion="1").text = url
    ET.SubElement(source, "allowsharing").text = "true"
    save_xml(path, root)
    dialog.ok(
        NAME,
        "Added %s.[CR]Restart Kodi, then open Videos > Files > %s. Kodi asks for the NAS login the "
        "first time. Use the menu button on the folder and choose Set content to scan it into the library." % (url, label),
    )


def use_skin():
    if xbmc.getSkinDir() == SKIN_ID:
        dialog.ok(NAME, "Lumen is already the active skin.")
    elif not has_addon(SKIN_ID):
        dialog.ok(NAME, "The Lumen skin is not installed. Install it from the Lumen Repository.")
    else:
        rpc("Settings.SetSettingValue", setting="lookandfeel.skin", value=SKIN_ID)


def toggle_menu():
    if xbmc.getSkinDir() != SKIN_ID:
        dialog.ok(NAME, "Switch to the Lumen skin first.")
        return
    kept = bool(xbmc.getCondVisibility("Skin.HasSetting(lumen_keep_menu)"))
    xbmc.executebuiltin("Skin.ToggleSetting(lumen_keep_menu)")
    xbmc.executebuiltin("ReloadSkin()")
    dialog.ok(NAME, "The side menu will now hide while you browse the rows." if kept
              else "The side menu will now stay on screen.")


def quick_setup():
    if not apply_profile():
        return
    if dialog.yesno(NAME, "Add a NAS share for local files?"):
        add_nas()
    if dialog.yesno(NAME, "Connect your Trakt account now? It powers the Watchlist and Up next rows."):
        connect_trakt()


def menu():
    items = [
        ("Quick setup (profile, NAS, Trakt)", quick_setup),
        ("Performance profile", apply_profile),
        ("Connect Trakt", connect_trakt),
        ("Default player for movies", lambda: choose_player("movie")),
        ("Default player for TV", lambda: choose_player("tv")),
        ("Add a NAS share", add_nas),
        ("Switch to the Lumen skin", use_skin),
        ("Side menu: auto-hide on/off", toggle_menu),
    ]
    while True:
        choice = dialog.select(NAME, [item[0] for item in items])
        if choice < 0:
            return
        items[choice][1]()
        if choice in (0, 2, 3, 4, 6):
            return  # these hand over to another dialog


if __name__ == "__main__":
    sync_trakt_rows()
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        pass  # the row check above is all this call is for
    elif len(sys.argv) > 1 and sys.argv[1] == "firstrun":
        xbmc.sleep(1500)  # let the home screen finish opening
        if dialog.yesno("Welcome to Lumen", "Run the quick setup now? You can open Lumen Setup from Add-ons at any time."):
            quick_setup()
    else:
        menu()
