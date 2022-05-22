# Demo application to control the computer's page down and page up keys from the
# RS24.

from pynput.keyboard import Controller, Key
from olympus import OlympusUSBHID, Transition

keyboard = Controller()

def button_press(name, transition):
    keymap = {
        'LISTEN': Key.page_down,
        'REW': Key.page_up
    }

    if name in keymap:
        if transition == Transition.PRESS:
            keyboard.press(keymap[name])
        elif transition == Transition.RELEASE:
            keyboard.release(keymap[name])

o = OlympusUSBHID()
o.register_handler('REW', Transition.BOTH, button_press)
o.register_handler('LISTEN', Transition.BOTH, button_press)

print('Olympus RS24 keyboard mapper. Press Ctrl+C to exit.')
o.start()
