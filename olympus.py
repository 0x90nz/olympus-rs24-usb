from enum import Enum
from time import sleep
import usb.core
import usb.util

class Transition(Enum):
    PRESS = 1
    RELEASE = 2
    BOTH = 3

class OlympusUSBHID():
    # Map of mask bits to default button properties
    DEFAULT_BUTTONMAP = {
        0x02: {'name': 'LISTEN'},
        0x04: {'name': 'REW'},
        0x08: {'name': 'FF'},
    }

    # Initialse the class, but don't initialise the device yet.
    #
    # handlers (optional):      map of (name, transition) to handler function
    # button_map (optional):    map of button bitmasks to properties
    # ignore_bitmap (optional): bitmap of bits to ignore when calculating
    #                           differences. On the RS24 bit 0 seems to indicate
    #                           no button pressed, so is a bit annoying, hence
    #                           it's ignored by default.
    # frame_index (optional):   the index into the frame at which the state is found
    # endpoint (optional):      the USB endpoint which is used to get the state
    def __init__(self, handlers={}, button_map=DEFAULT_BUTTONMAP, ignore_bitmap=0x01, frame_index=2, endpoint=0x83):
        self._button_map = button_map
        self._handlers = handlers
        self._state = 0
        self._ignore_bitmap = ignore_bitmap
        self._frame_index = frame_index
        self._endpoint = endpoint

    # Register a handler function for a transition (or both).
    #
    # name:         the name of the button
    # transition:   the transition for the function to be called on
    # fn:           the function to call on the transition
    def register_handler(self, name: str, transition: Transition, fn):
        self._handlers[(name, transition)] = fn

    # internal setup function, find & init device, set some parameters based on
    # the descriptor we get back.
    def _setup(self):
        # Find Olympus RS24
        dev = usb.core.find(idVendor=0x07b4, idProduct=0x0202)

        # Did we find it?
        if dev is None:
            raise ValueError('Device not found')

        # Setup & getting config values
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        interrupt_ep = cfg[(0,0)][2]

        self._packet_size = interrupt_ep.wMaxPacketSize
        self._dev = dev
        self._poll_interval = interrupt_ep.bInterval * 0.001

    # Begin polling the device for changes in state.
    #
    # This function will loop forever, until interrupted.
    def start(self):
        self._setup()

        while True:
            frame = self._dev.read(self._endpoint, self._packet_size)

            # Ignore any bits we don't want to use
            state = frame[self._frame_index] & ~self._ignore_bitmap

            if state != self._state:
                diffs = state ^ self._state

                for mask, btn in self._button_map.items():
                    # did this value change?
                    if diffs & mask:
                        transition = Transition.PRESS if state & mask else Transition.RELEASE
                        name = btn['name']

                        if (name, transition) in self._handlers:
                            self._handlers[(name, transition)](name, transition)
                        elif (name, Transition.BOTH) in self._handlers:
                            self._handlers[(name, Transition.BOTH)](name, transition)

            self._state = state
            sleep(self._poll_interval)
