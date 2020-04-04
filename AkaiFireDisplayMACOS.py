"""This script was written by Josh Ball for Kornelius Paede to facilitate in the formatting of SysEx messages to the display
text on the OLED screen of an Akai Fire MIDI controller. Credit to Paul Curtis from Segger for his research and testing
and his extensive blog where he documents his process. Both the PlotPixel and GenerateBitmap functions have been
converted into Python from his original code, without which the task of writing this script would have been considerably
more difficult. Due to the technical nature of this script, and the lack of intensive testing - no warranty is given
or implied, it is distributed freely to anyone that can make use of it. Any questions relating to this script can be
directed to Josh from Flowstate. CC 4.0 Share Alike"""

#######################################################################################################################
# Import

#Requires Python Pillow package for generating Bitmaps

import os, re, subprocess, socket
from PIL import Image, ImageDraw, ImageFont, ImageOps

#######################################################################################################################
# Global Variables

# First generate an available port number using socket - this is necessary to avoid waiting for the port to finish
# terminating after disconnect.

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 0))
s.listen(1)
port = s.getsockname()[1]  # This will the port number that is used to listen for input from PureData
s.close()

# Get a path to puredata


for app in os.listdir('/Applications'):
    if 'Pd-0.50' in app:
        pd = app
        break

path = '/Applications/{0}/Contents/Resources/bin/'.format(pd)


# Create the blank image and drawing
W, H = (128, 56)
IMG = Image.new('1', (W, H), color=0)
d = ImageDraw.Draw(IMG)

# This will be used to chose a line for the text 1 - 4
Y_ALIGN = {1: 0,
           2: 14,
           3: 28,
           4: 42}

# Create a dictionary that will be used to select the typeface, this can be expanded if need.

FontDict = {'arial': 'Pillow/Tests/fonts/Arial.ttf',
            'verdana': 'Pillow/Tests/fonts/Verdana.ttf',
            'times': 'Pillow/Tests/fonts/Times New Roman.ttf'}

# Pixel re-mapping order

BitMutate = [[13, 19, 25, 31, 37, 43, 49],
             [0, 20, 26, 32, 38, 44, 50],
             [1, 7, 27, 33, 39, 45, 51],
             [2, 8, 14, 34, 40, 46, 52],
             [3, 9, 15, 21, 41, 47, 53],
             [4, 10, 16, 22, 28, 48, 54],
             [5, 11, 17, 23, 29, 35, 55],
             [6, 12, 18, 24, 30, 36, 42]]

# Create a list of size 1175 to store the converted bytes in

BitMap = [0 for i in range(1175)]


#######################################################################################################################
# Functions


def clear_screen():
    IMG = Image.new('1', (W, H), color=0)
    IMG.save('test.bmp', 'bmp')  # This saves a test image to show how the display should look
    byte_map = list(IMG.tobytes())
    to_ints = [ord(byte) for byte in byte_map]
    return to_ints



def make_bits_from_text(text, line, align, fontsize, typeface, negative):
    """ This function generates a bitmap. It takes arguments for the text, line, alignement, fontsize, typeface and
    if negative. These are used to generate a 128 x 56 monochrome image using Pillow, which is then converted to bytes
    before finally being converted to a list of integers and returned"""

    if int(fontsize) > 14:
        fontsize = 14

    if negative == 'true':
        text_color = 0
        bg_color = '#ffffff'
        outline_color = 'white'
    else:
        text_color = 1
        bg_color = '#000000'
        outline_color = 'black'

    try:
        fnt = ImageFont.truetype(FontDict[typeface], int(fontsize))
    except KeyError:
        fnt = ImageFont.truetype(FontDict['arial'], int(fontsize))
    except TypeError:
        fnt = ImageFont.truetype(FontDict[typeface], 14)



    w, h = d.textsize(text, font=fnt)
    X_ALIGN = {'left': 2,
               'centre': (W - w) / 2,
               'right': (W - w) - 2}
    try:
        x = X_ALIGN[align]
        y = Y_ALIGN[int(line)]
    except KeyError:
        x = X_ALIGN['left']
        y = Y_ALIGN[1]
    shape = [(0, y), (127, y + 16)]
    d.rectangle(shape, fill=bg_color, outline=outline_color)
    d.text(xy=(x, y), text=text, font=fnt, fill=text_color)
    flipped = ImageOps.flip(IMG)
    IMG.save('test.bmp', 'bmp') # This saves a test image to show how the display should look
    byte_map = list(flipped.tobytes())
    to_ints = [ord(byte) for byte in byte_map]
    return to_ints


def PlotPixel(x, y, c):
    """This function plots the bits to there new position and values, using bitwise operation to move the bits along
    while setting them to the correct index of the BitMap list"""

    if x < 128 and y < 64:
        x += 128 * (y // 8)
        y %= 8
        remap_bit = BitMutate[int(y)][int(x % 7)]
        if c > 0:
            BitMap[4 + int(x // 7 * 8) + int(remap_bit // 7)] |= 1 << (int(remap_bit % 7))
        else:
            BitMap[4 + int(x // 7 * 8) + int(remap_bit // 7)] &= ~(1 << (int(remap_bit % 7)))
    return


def GenerateBitMap(arguments):
    """This function makes a new bitmap using nested loops for x and y of available bit positions, then re-plots them
    using the PlotPixel function above"""

    if len(arguments) == 1 and arguments[0] == 'clear':
        try:

            bits = clear_screen()
        except TypeError:
            print(arguments)
            return
    else:
        try:
            bits = make_bits_from_text(*arguments)
        except TypeError:
            print(arguments)
            return

    for x in range(128):
        for y in range(64):
            PlotPixel(x, y, 0)
    for y in range(56):
        for x in range(120):
            if bits[(55 - y) * int(128 // 8) + int(x // 8)] & (0x80 >> (x % 8)):
                PlotPixel(x + 4, y + 4, 1)
    return BitMap


def create_sysex_message(arguments):
    """This function creates the sysex message using the functions above, it combines the generated bitmap with the
    appropriate prefix and other messages, then converts this to the appropriate format and sends it to the function
    that communicates with puredata"""
    new_bit_map = GenerateBitMap(arguments)
    sysex_prefix = [240, 71, 127, 67, 14]
    start_message = [len(new_bit_map) >> 7]
    end_message = [len(new_bit_map) & 0x7F]
    sysex_end = [247]
    new_bit_map[:-1171] = [0, 7, 0, 127]
    MESSAGE = sysex_prefix + start_message + end_message + new_bit_map + sysex_end
    print (MESSAGE)
    strings = (str(byte) for byte in MESSAGE)
    message_to_send = ' '.join(strings) + ';'
    send_to_pd(message_to_send)


def receive_from_pd():

    """This function is called to start the script. It opens a tcp connection with puredata where it constantly listens
    for input, it uses the port generated using socket to do this. It also sends a connect message to puredata on port
    3001, telling puredata to send information on the generated available port. Port 3001 is used to send data to pure
    data, and the generated port is used to send data to this script."""

    send_to_pd('c connect localhost {0};'.format(port))
    while True:
        try:
            next_line = process.stdout.readline()
            if next_line:
                print(next_line)
                incoming_data = re.findall('"([^"]*)"', next_line)
                create_sysex_message(tuple(incoming_data))
                print(tuple(incoming_data))

        except KeyboardInterrupt:
            send_to_pd('c disconnect;')
            process.terminate()
            return


def send_to_pd(message=''):
    """This function sends a message over pdsend on port 3001, it is used to send a connect and disconnect message, as
    well as to send the final sysex message"""

    os.system("echo '" + message + "' | {0}pdsend 3001".format(path))


########################################################################################################################


# Run Program

# First create the subprocess that will listen to pdreceive on the port generated by socket.

process = subprocess.Popen([path + 'pdreceive', str(port)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Then open the other connections and start receiving data, line by line.

receive_from_pd()


