# A bluetooth controlled, skid-steer robot. In MicroPython.
# Mark Goodwin. 2013 - 2024
from machine import Pin,UART,PWM,Timer

# Connectivity: Set up UART 1, GPIO pins 4 and 5 (physical pins 6 and 7)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5)) # 9600 baud
uart.init(bits=8, parity=None, stop=1) # 8n1

# Move the motor attached to the specified PWM Pins
def move_motor(speed, forward_pin, reverse_pin):
    speed = int((speed / 255) * 65025)
    if 0 <= speed:
        forward_pin.duty_u16(abs(speed))
        reverse_pin.duty_u16(0)
    else:
        forward_pin.duty_u16(0)
        reverse_pin.duty_u16(abs(speed))

# Outputs: Motor outputs; PWM on pins 0,1,2,3
LF = PWM(Pin(0)) # GPIO pin 0, physical pin 1
LR = PWM(Pin(1)) # GPIO pin 1, physical pin 2
RF = PWM(Pin(2)) # GPIO pin 2, physical pin 4
RR = PWM(Pin(3)) # GPIO pin 3, physical pin 5

# Set the frequencies for all PWM pins
[pin.freq(1000) for pin in (LF,LR,RF,RR)]

# Ensure the motors are *off* to start with (this is
# really helpful to ensure misbehaving controllers are
# easily corrected
move_motor(0, LF, LR)
move_motor(0, RF, RR)

# Read data from the uart (run from a timer)
def read_serial(timer):
    if uart.any(): 
        data = uart.read()
        lines = [line.strip() for line in data.decode().split('\n')]
        for line in lines:
            if(len(line) > 0):
                # for _reasons_, the phone app sends X,Y coordinates, 1 per line
                # as UTF-8 strings. X and Y are values, nominally between 0 and 512
                xs, ys = line.split(',')
                # Turn these into 'steering' and 'throttle' integer values, centred
                # at 0
                steering, throttle = int(xs) - 255, int(ys) - 255
                print(steering, throttle)
                # Clip the steering ceiling if the control is hard forward
                ceiling = 255 - abs(steering)
                # if the throttle magnitude is greater than the ceiling, clip the throttle
                if abs(throttle) > ceiling:
                    if 0 > throttle:
                        throttle = -1 * ceiling
                    else:
                        throttle = ceiling
                # Calculate the left and right components for motor movement
                left = throttle - steering
                right = throttle + steering
                # Move the motors!
                move_motor(left, LF, LR)
                move_motor(right, RF, RR)

# Create a periodic timer at 25Hz, calling read_serial
t = Timer()
t.init(freq=25, mode=Timer.PERIODIC, callback=read_serial)