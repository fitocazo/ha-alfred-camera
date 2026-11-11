"""Camera selection helpers independent of Home Assistant."""

def selected_cameras(entry):
    """Prefer options while retaining compatibility with existing entries."""
    return list(entry.options.get("cameras", entry.data.get("cameras", [])))


def camera_options(devices, selected):
    """Keep selected IDs even if Alfred temporarily omits a camera."""
    choices = {}
    for device in devices:
        camera_id = device.get("_id")
        if isinstance(camera_id, str) and camera_id:
            choices[camera_id] = str(device.get("label") or camera_id)
    for camera_id in selected:
        choices.setdefault(camera_id, camera_id)
    return [{"value": camera_id, "label": label} for camera_id, label in choices.items()]
