"""UI bookmark coordinates, not verified boundaries or traffic observations."""
BOOKMARKS = {
    "iasi-demo-intersection": ("Intersecție sintetică", (27.584, 47.153)),
    "podu-ros": ("Podu Roș — context DEMO", (27.584, 47.153)),
    "copou": ("Copou — context DEMO", (27.568, 47.184)),
    "centru": ("Centru — context DEMO", (27.586, 47.162)),
    "tatarasi": ("Tătărași — context DEMO", (27.613, 47.169)),
    "alexandru": ("Alexandru cel Bun — context DEMO", (27.548, 47.169)),
}


def bookmark(area_id):
    key = area_id.removeprefix("preview-").removeprefix("iasi-")
    return BOOKMARKS.get(area_id) or BOOKMARKS.get(key)
