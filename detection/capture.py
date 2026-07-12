import numpy as np
import mss

def grab_screen(monitor_index=1):

    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        raw = sct.grab(monitor)

        frame = np.array(raw)
        frame = frame[:, :, :3][:, :, ::-1]  # BGRA > BGR > RGB
        return frame
 
def grab_region(left, top, width, height):

    with mss.mss() as sct:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        raw = sct.grab(monitor)
        frame = np.array(raw)
        frame = frame[:, :, :3][:, :, ::-1]
        return frame