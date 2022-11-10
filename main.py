from cefpython3 import cefpython as cef
import os
import platform
import subprocess
import sys
import tkinter as tk

try:
    from PIL import image
except ImportError:
    print("Pip is not install"
    "instal using: pip install PIL")
    sys.exit(1)

def main(url, w, h):
    global VIEWPORT_SIZE, URL, SCREENSHOT
    URL = url
    VIEWPORT_SIZE = (w, h)
    SCREENSHOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "SCREENSHOT.png")

    check_versions()
    sys.excepthook = cef.ExceptHook()

    if os.path.exists(SCREENSHOT):
        print("Remove old screenshot")
        os.remove(SCREENSHOT)

    command_line_arguments()

    settings = {
        "windowless_rendering_enabled": True,
    }

    switch = {
        "disable-gpu": "",
        "disable-gpu-compositing": "",
        "enable-begin-frame-scheduling": "",
        "disable-surface": "",
    }

    browser_settings = {
        "windowless_frame_rate": 30,
    }

    cef.Initialize(settings=settings, switches=switch)
    create_browser(browser_settings)
    cef.MessageLoop()
    cef.Shutdown()
    print("Opening your screenshot with the default application")
    open_with_default_application(SCREENSHOT)


def check_versions():
    ver = cef.GetVersion()
    print("CEF Python {ver}".format(ver=ver["version"]))
    print("Chromium {ver}".format(ver=ver["chrome_version"]))
    print("CEF {ver}".format(ver=ver["cef_version"]))
    print("Python {ver} {arch}".format(ver=platform.python_version(),
                                       arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


def command_line_arguments():
    if len(sys.argv) == 4:
        url = sys.argv[1]
        width = int(sys.argv[2])
        height = int(sys.argv[3])
        if url.startswith(("http://")) or url.startswith("https://"):
            global URL
            URL = url
        else:
            print("Error : Invalid URL Entered")
            sys.exit(1)
        if width > 0 and height > 0:
            global VIEWPORT_SIZE
            VIEWPORT_SIZE = (width, height)
        else:
            print("Error: Invalid width and height")
            sys.exit(1)
    elif len(sys.argv > 1):
        print("Error : Expected Arguments Not Received")


def create_browser(settings):
    global VIEWPORT_SIZE, URL
    parent_window_hadle = 0
    window_info = cef.WindowInfo()
    window_info.SetAsOffscreen(parent_window_hadle)
    print("Viewport size : {size}".format(size=str(VIEWPORT_SIZE)))
    print("Loading URL : {url}".format(url=URL))
    browser = cef.CreateBrowserSync(window_info=window_info, settings=settings, url=URL)
    browser.SetClientHandler(LoadHandler())
    browser.SetClientHandler(RenderHandler())
    browser.SendFocusEvent(True)
    browser.WasResized()


def save_screenshot(browser):
    global SCREENSHOT
    buffer_string = browser.GetUserData("OnPaint.buffer string")
    if not buffer_string:
        raise Exception("Buffer String was empty")
        image = Image.frombytes("RGBA", VIEWPORT_SIZE, buffer_string, "raw", "RGBA", 0, 1)
        image.save(SCREENSHOT, "PNG")
        print("Saved screenshot to: {path}".format(path=SCREENSHOT))


def open_with_default_application(path):
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile((path))
    elif os.name == "posix":
        subprocess.call("xdg-open", path)


def exit_app(browser):
    print("Closing Browser")
    browser.CloseBrowser()
    cef.QuitMessageLoop()


class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        if not is_loading:
            sys.stdout.write(os.linesep)
            print("Website has been Loaded")
            save_screenshot()
            cef.PostTask(cef.TID_UI, exit_app, browser)

    def OnLoadError(self, browser, frame, error_code, failed_url, **_):
        if not frame.IsMain():
            return
        print("Failed to load URL : {url}".format(url=failed_url))
        print("Error code : {code}".format(code=error_code))
        cef.PostTask(cef.TID_UI, exit_app, browser)


class RenderHandler(object):
    def __init__(self):
        self.Onpaint_called = False

    def GetViewRect(self, rect_out, **_):
        rect_out.extend([0, 0, VIEWPORT_SIZE[0], VIEWPORT_SIZE[1]])
        return True

    def OnPaint(self, browser, element_type, paint_buffer, **_):
        if self.Onpaint_called:
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            sys.stdout.write("OnPaint")
            self.Onpaint_called = True
        if element_type == cef.PET_VIEW():
            buffer_string = paint_buffer.GetBytes(mode="rgba", origin="top-left")
            browser.SetUserData("OnPaint.buffer_string", buffer_string)
        else:
            raise Exception("Unsuported element")


root = tk.TK()
root.geometry("400x200")


class Widgets:
    def __init__(self, lab_text, set_variable):
        self.lab = tk.Label(root, text=lab_text)
        self.lab.pack()
        self.v = tk.StringVar()
        self.entry = tk.Entry(root, textvariable=self.v)
        self.entry.pack()
        self.v.set(set_variable)


obj_1 = Widgets("Enter Website Name: ", "https://www.google.com/")
obj_2 = Widgets("Enter Width:", "1000")
obj_3 = Widgets("Enter Height:", "500")
root.bind("<Return>", lambda x: main(obj_1.v.get()), int(obj_2.v.get()), int(obj_3.v.get()))

lab_4 = tk.Label(root, text="")
lab_4.pack()

lab_5 = tk.Label(root, text="Press the Enter to create Screenshot")
lab_5.pack()

root.mainloop()





