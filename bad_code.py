# The following is some very bad code.
# Not only are there lots of bugs, but lots of bad design decisions too.
# Keep an eye out for both.

### Hey, it's Patrick Melanson. I did a couple go-overs of the code,
### and I only left comments (all starting with ###).
### However, I can't spend more time on this code review, because
### one weekend isn't much time, esp. since I have two assignments on Monday.
### Sorry if I didn't catch all the bugs and bad design decisions in the
### couple minutes I had. See you!

from serial import Serial
from threading import Thread, Lock
import time ### is time needed? it's not used.
import sys ### similarly, this is just imported
import os
import struct
from datetime import datetime


class CentrifugeController:
    at_speed = False    ### this doesn't get used, why is this here?
    ### this would be better as a method, since one might forget to set
    ### this variable when speed is reached
    target_speed = None

    _speeds = []
    _speed_cap = 10000
    _vibration_callback = None
    reconnect = True

    ### should have _cycle_running up with the rest of the class variables
    def __init__(self):
        self._cycle_running = False

    def connect(self, port):
        self.port = Serial(port, timeout=1)
        self.port_lock = Lock()
        self._cycle_running = False
        # Check that we're connected to the right device
        self.port.write("?")
        buffer = ""
        while True:
            res = self.port.read()
            buffer += res
            if not res:
                break
        if res != "Serial Centrifuge 8.1":
            raise ValueError("You connected to something that wasn't a centrifuge")

    ### have disconnect only disconnect, and have a separate reconnect method
    def disconnect(self):
        self.port.close()
        ### ie move this into its own method
        if self.reconnect:
            self.connect()
            # reset our speed to what it was before
            self.speed(self._speed_cap)

    def speed(self, speed):
        self.port_lock.acquire()
        self.port.write("Speed: " + speed + "RPM\n")
        self.port_lock.release()

    def get_speed_in_thread(self):
        # Make sure nobody is using the port
        self.port_lock.acquire()
        # Ask the device its current speed
        self.port.write("Speed?\n")
        # Wait for response
        result = self.port.read(8)
        if result == b"VIBRTION":
            # Too mcuh vibration - shut everything down ASAP before damage occurs
            if self._vibration_callback:
                self._vibration_callback()
            self.speed(0)
            self.disconnect()
            raise RuntimeError("Excessive vibration - cycle halted")
        # Remove 'RPM' from the end
        result = result[:-4]
        self.got_speed = result
        # Release the port lock so others can use it
        self.port_lock.release()

    ### inconsistent naming scheme, getSpeed is camelCase
    ### but other methods are under_scores
    def getSpeed(self):
        thread = Thread(target=self.get_speed_in_thread)
        thread.start()

    def perform_centrifuge_cycle(self, name, cycle):
        # Dont start if door is open
        if self.is_door_closed() == "no":
            return "door not closed"
        self._cycle_running = True
        for step in cycle.split("\n"):
            s = int(step.split(" for ")[0][:-3])
            t = int(step.split(" for ")[1][:-8])
            if s > self._speed_cap:
                continue
            self.speed(s)
            # Wait for it to get to our desired speed
            self.target_speed = s
            while not self.got_speed > self.target_speed:
                self.getSpeed()
            # Run at our desired speed for the given t
            start_wait = datetime.now()
            while (datetime.now() - start_wait).total_seconds() < t:
                pass

        self._cycle_running = False
        os.shell("net send localhost \"Done cycle " + name + '"')

    ### ugh, four different functions with slightly different literals.
    ### refactor suggestion: merge all of these four into
    ### speed_change(self, amnt) and if you want to keep the ability
    ### to call a small or large increase, define constants
    ### 'SMALL_INC' 'LARGE_DEC' or some such and pass them to
    ### self.speed_change(amnt). Having predefined constants is good
    ### though, makes sure that there is a consistent standard for
    ### increasing and decreasing speed. Having multiple speed
    ### increase and decrease functions is not good, because a)
    ### bad code smell, b) code duplication is avoidable, and c)
    ### it relies on magic numbers more
    def speed_increase_small(self):
        self.speed(self.got_speed+10)

    def speed_increase_lg(self):
        self.speed(self.got_speed+100)

    def speed_decrease_small(self):
        self.speed(self.got_speed-10)

    def speed_decrease_lg(self):
        self.speed(self.got_speed+100)

    def is_door_closed(self):
        self.port.write("Door Open?")
        return self.port.read(1)

    def manual_control(self, command):
        speed = int(command.split(" for ")[0][:-3])
        if speed > self._speed_cap:
            return
        ### time is conflicting with imported module, but there is no reason
        ### for there to be an 'import time' since time is not used
        ### so just remove 'import time'
        time = int(command.split(" for ")[1][:-8])
        self.speed(speed)
        # Wait for it to get to our desired speed
        self.target_speed = speed
        while not self.got_speed > self.target_speed:
            self.getSpeed()
        # Run at our desired speed for the given time
        time.sleep(time)

    def vib_callback(self):
        self.did_vibrate = True

    def find_max_speed_before_vibration(self):
        # speed = 10
        # self._vibration_callback = self.vib_callback
        # while speed < self._speed_cap:
        #     # Set the speed
        #     self.speed(speed)
        #     if input("is the centrifuge on the floor?"):
        #         return speed
        #     speed = speed + 100

        speed = 10
        self._vibration_callback = self.vib_callback
        while speed != self._speed_cap:
            # Set the speed
            self.speed(speed)
            # Wait to see if we get a vibration error
            test_start = datetime.now()
            while (datetime.now() - test_start).total_seconds() < 10:
                try:
                    self.get_speed_in_thread()
                except:
                    pass
                if self.did_vibrate:
                    return speed
            speed = speed + 100

    def log_speed(self, speed):
        self._speeds.append((datetime.now(), speed))
        self.save_log()

    def average_speed(self):
        ### as currently written, this function will not find average speed
        ### over time. Instead, you have to weight each element in self._speeds
        ### by how long it was at that speed. A working algorithm
        ### will also take into account the current cycle (if this is desired
        ### behaviour), then integrate from t=0 to t=datetime.now() To get
        ### total distance traveled, then divide by datetime.now() to get
        ### the actual mean speed.
        accum = 0
        for e in self._speeds:
            accum = accum + e[1]
        average = accum / len(self._speeds)
        return average

    def speed_standard_dev(self):
        # accum = 0
        # for e in self._speeds:
        #     accum = accum + e[1]
        # average = accum / len(self._speeds)
        # deviation = 0
        # last_speed = None
        # for e in self._speeds:
        #     if last_speed:
        #         deviation += e[1] - last_speed
        #     last_speed = e[1]
        # return deviation

        ### kay, so like you already have a function for determining average
        ### speed, cut down on (buggy) code duplication and just have
        ### average = self.average_speed()
        accum = 0
        for e in self._speeds:
            accum = accum + e[1]
        average = accum / len(self._speeds)
        ### similarly to the bug in average_speed(), this isn't being
        ### weighted for how long the centrifuge is at a current speed.
        ### a fixed algorithm is to calculate the variance of all elements
        ### in self._speeds (and also account for the current speed setting)
        ### by taking each speed, calculating difference from the mean,
        ### squaring the difference, then multiplying by the time for which
        ### the speed was set at. Sum the result of this for all speeds (and
        ### account for current speed), take the square root and you have the SD
        ### wow tada
        deviation = 0
        for e in self._speeds:
            deviation += e[1] - average
        return deviation

    def max_speed(self):
        max_speed = 0
        for e in self._speeds:
            max_speed = max(max_speed, e[1])
        return max_speed

    def is_running(self):
        return self._cycle_running

    def save_log(self):
        import calendar ### why have an import in a function?
        ### logging is a common function, so just import calendar once up top
        ### however, I don't know how often this function will be called.
        ### every few seconds? Once every few runs? Whether or not
        ### import calendar stays in depends on that answer.
        log_f = open("logs\speed.log", "wb")
        log_f.write(b'SC8.1')
        for e in self._speeds:
            log_f.write(struct.pack("<HH", int(calendar.timegm(e[0].utctimetuple())), e[1]))


Controller = CentrifugeController()
Controller.connect("/dev/hypothetical.usb.centrifuge")
### refactor command with JSON? more params?
Controller.perform_centrifuge_cycle("Blood samples", """3500RPM for 60 seconds
1000RPM for 120 seconds
5000rpm for 10.5 seconds
""")
