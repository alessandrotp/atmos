"""Plot the facilities from main.xlsx on an interactive map.

Usage:
    python sources/map_facilities.py [input.xlsx] [output.html]

By default it reads intermediate/main.xlsx, writes facilities_map.html in the
repository root and opens it in the default browser.
"""
import html
import sys
import webbrowser
from pathlib import Path

import folium
import pandas as pd

HERE = Path(__file__).parent        # <repo>/sources
REPO = HERE.parent                  # <repo>
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "intermediate" / "main.xlsx"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "facilities_map.html"

MARKER_COLOR = "#e31a1c"

# Number shown on each marker for the unit types a facility contains
UNIT_TYPE_CODES = {
    "port_terminal": "1",
    "crude_distillation": "2",
    "steam_cracker_naphtha": "3",
}

df = pd.read_excel(SRC, dtype=str, keep_default_na=False)
df = df.rename(columns={"facility_id": "id"})

unknown = set(df["unit_type"]) - set(UNIT_TYPE_CODES) - {""}
if unknown:
    print(f"Unit types without a code (ignored): {sorted(unknown)}")
# e.g. a facility with a terminal and a cracker -> "13"
codes = df.groupby("id")["unit_type"].agg(
    lambda types: "".join(sorted({UNIT_TYPE_CODES[t] for t in types if t in UNIT_TYPE_CODES}))
)

# main.xlsx has one row per unit; keep one row per facility
df = df.drop_duplicates(subset="id")
df["code"] = df["id"].map(codes)
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

missing = df[df["latitude"].isna() | df["longitude"].isna()]
if not missing.empty:
    print(f"Skipping {len(missing)} facilities without coordinates")
df = df.drop(missing.index)

# Esri tiles work from a local file; OpenStreetMap's servers block pages
# opened from disk (no Referer header) with a 403 "Access blocked" tile.
fmap = folium.Map(tiles=None)
folium.TileLayer("Esri.WorldStreetMap", name="Streets").add_to(fmap)
folium.TileLayer("Esri.WorldImagery", name="Satellite").add_to(fmap)

# One toggleable layer per unit-type code (1, 2, 3; combos like "13" get their own)
CODE_NAMES = {c: t for t, c in UNIT_TYPE_CODES.items()}
layers = {}
for code in sorted(df["code"].unique()):
    count = (df["code"] == code).sum()
    name = f"{code or 'No units'}" + (f" – {CODE_NAMES[code]}" if code in CODE_NAMES else "")
    layers[code] = folium.FeatureGroup(name=f"{name} ({count})").add_to(fmap)

for row in df.itertuples(index=False):
    parent = row.parent_organization_id or "<i>none</i>"
    popup = (
        f"<b>{html.escape(row.name)}</b><br>"
        f"ID: {html.escape(row.id)}<br>"
        f"Country: {html.escape(row.country_code)}<br>"
        f"Status: {html.escape(row.status)}<br>"
        f"Unit types: {row.code or '<i>none</i>'}<br>"
        f"Parent org: {parent if not row.parent_organization_id else html.escape(parent)}<br>"
        f"Coordinates: {row.latitude:.4f}, {row.longitude:.4f}"
    )
    size = 18 + 7 * max(len(row.code) - 1, 0)
    label = (
        f'<div style="width:{size}px;height:18px;line-height:18px;border-radius:9px;'
        f"background:{MARKER_COLOR};color:#fff;border:1px solid #fff;"
        f'font:bold 11px Arial,sans-serif;text-align:center;box-shadow:0 0 2px #000">'
        f"{row.code}</div>"
    )
    folium.Marker(
        location=[row.latitude, row.longitude],
        icon=folium.DivIcon(html=label, icon_size=(size, 18), icon_anchor=(size // 2, 9)),
        tooltip=row.name,
        popup=folium.Popup(popup, max_width=320),
    ).add_to(layers[row.code])

folium.LayerControl(collapsed=False).add_to(fmap)
fmap.fit_bounds([
    [df["latitude"].min(), df["longitude"].min()],
    [df["latitude"].max(), df["longitude"].max()],
])

fmap.save(OUT)
print(f"Mapped {len(df)} facilities -> {OUT}")
webbrowser.open(OUT.resolve().as_uri())
