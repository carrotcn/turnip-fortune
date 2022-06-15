# turnip-fortune

This program helps you find an ideal selling price of turnip in the Nintendo Switch game Animal Crossing: New Horizon (ACNH). Team up with your friends and make a fortune! 

## How it works

- In ACNH, the turnip selling price varies upon changes of system time. 
- The program automates the seeking of high selling price by iterating through a predefined list of button and joystick actions.
- Actions in the list control the character moving, dialog options and the change of system time in Nintendo Switch's OS settings menu to trigger the change of turnip price. Note that the list of actions needs to be adjusted, as:
  - The relative location of house and shop varies on each ACNH island depending on how players have been designing the island layout. Character needs a pre-defined routine to navigate from initial position (in front of one's home) to the shop to check the price.
  - Switch system and/or ACNH game updates may cause dialog, menu items, and options in Settings to change. In-game loading time might also be affected. 
		
- Actions are sent to a Teensy++ 2.0 board via serial port. There is a separate C program running on Teensy that emulates itself as a JoyCon and translates the input from serial port to actual button and joystick events. 
- Teensy is connected to the dock of Nintendo Switch via USB cable. Wired solution is favored here as opposed to other controller emulation technique over Bluetooth for maximum stability, considering the program will typically take hours to run without human intervention, before the desirable price shows up.
- The program gets its vision of the screen content via an Elgato HD60S+ capture card that reads the HDMI output from Nintendo Switch dock.
- OCR is applied with Tesseract based on a model specifically trained to recognize the fonts and characters in ACNH dialog (language: Simplified Chinese), in order to determine the current selling price of turnip.
- The program iterates until the selling price becomes higher than the set limit.
- Email notification will be triggered in the event of program exit or error.

## Preparation

- Install Elgato 4K Capture Utility
- Download and install [Tesseract] (https://tesseract-ocr.github.io/tessdoc/Home.html)
- Maintain the *acnh_config.ini* configuration file. Refer to *acnh_config.ini.example*.
  - price_threshold: self-explanatory.
  - tessdata_dir: path to the language data files that has been trained to recognize the turnip price (based on Simplified Chinese as ACNH's display language) in configuration file.
  - tesseract_cmd: path to Tesseract executable.
  - cap_dir: path to the cap folder, where the program writes the screenshots and log file.
  - com_port: COM port used for communication between the python program and Teensy.
  - GMAIL_NOTIFICATION_USR: gmail address used by the program to send mail notification.
  - GMAIL_NOTIFICATION_PWD: password of the gmail account used to send mail notification.
  - DEV_MAIL_RECIPIENT: recipient list of notification.
- Install python packages: ``` python -m pip install pytesseract pyserial colormath pywin32 brotli ```

## How to use

1. Start ACNH on the Switch and leave your character exactly in its initial state in front of the house after loading.
2. Press HOME button on your physical controller to go back to the system menu (game selection screen).
3. Connect Teensy to dock via USB cable. Upon connection Teensy will run the initialization script to take over as the controller. Wait till it finishes.
4. Once Teensy takes over, it brings you back to the game where your character is still standing in its initial position. Send via any serial port debugging tool !17@5# to let Teensy press the HOME button and go back to the system menu (game selection screen). 
5. Start the python program. The program will send ^ via serial port to let Teensy rerun the initialization (so that you don't need to unplug and plug in the Teensy every time you start the python program later on).
