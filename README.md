# Fire-Display
Python script combined with a PureData patch the facilitates writing to the display of an Akai Fire MIDI controller.
Written in Python 2.7. Usage instructions are contained within the PureData patch. 

This was written for a client who is doing some stuff with an Akai Fire to create a groove box, I've shared it here with his permission.

Credit for this script goes to Paul Curtis from Segger, without whom I would have had a considerable ammount more work to do.

He first decoded the strange layout of the display and SysEx message format and documented this extensively in his blog. The magis is in his original functions.

I have translated them into Python and built a script around this to handle arguments so that formatted text can be output on the screen.

Currently only MacOS.

To Do:

Error Handling
Different OS Handling
