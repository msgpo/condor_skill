from os.path import dirname
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.util.log import LOG

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

import re

__author__ = 'PCWii'

# Logger: used for debug lines, like "LOGGER.debug(xyz)". These
# statements will show up in the command line when running Mycroft.
LOGGER = getLogger(__name__)


# The logic of each skill is contained within its own class, which inherits
# base methods from the MycroftSkill class with the syntax you can see below:
# "class ____Skill(MycroftSkill)"
class CondorSkill(MycroftSkill):

    # The constructor of the skill, which calls Mycroft Skill's constructor
    def __init__(self):
        super(CondorSkill, self).__init__(name="CondorSkill")
        self.myKeywords = []
        self.client = mqtt.Client()

    # This method loads the files needed for the skill's functioning, and
    # creates and registers each intent that the skill uses
    def initialize(self):
        self.io_pins = [3, 5, 7, 29, 31, 26, 24, 21, 19, 23, 32, 33, 8, 10, 36, 11, 12, 35, 38, 40, 15, 16, 18, 22, 37, 13]
        GPIO.setmode(GPIO.BOARD)
        self.load_data_files(dirname(__file__))


    @intent_handler(IntentBuilder("GPIOIntent").require("GpioKeyword").
                    one_of("OnKeyword", "OffKeyword").build())
    def handle_gpio_intent(self, message):
        str_limits = []
        str_remainder = str(message.utterance_remainder())
        if (str_remainder.find('for') != -1) or (str_remainder.find('four') != -1):
            str_limits = [4]
        else:
            str_limits = re.findall('\d+', str_remainder)

        if str_limits:
            gpio_request = int(str_limits[0])
            if (gpio_request > 1) and (gpio_request < 28):
                pin_index = gpio_request - 2
                board_pin = self.io_pins[pin_index]
                LOG.info('The pin number requested was: ' + str(board_pin))
                if "OnKeyword" in message.data:
                    self.gpio_on(board_pin, gpio_request)
                if "OffKeyword" in message.data:
                    self.gpio_off(board_pin, gpio_request)
            else:
                self.speak_dialog("error", data={"result": str(gpio_request)})
        else:
            self.speak('No GPIO Pin was specified')

    @intent_handler(IntentBuilder("WikiIntent").require("TellKeyword").
                    require("AboutKeyword").require("ConestogaKeyword").build())
    def handle_wiki_intent(self, message):
        LOG.info('Condor.ai was asked: ' + str(message.uterance()))
        self.send_MQTT('Condor.ai was asked: ' + str(message.uterance()))
        str_remainder = str(message.utterance_remainder())
        # self.speak_dialog("about", data={"result": str(gpio_request)})
        self.speak_dialog("about")

    @intent_handler(IntentBuilder("AcademicIntent").require("WhatKeyword").
                    require("AcademicKeyword").optionally("ConestogaKeyword").build())
    def handle_academic_intent(self, message):
        LOG.info('Condor.ai was asked: ' + str(message.uterance()))
        self.send_MQTT('Condor.ai was asked: ' + str(message.uterance()))
        str_remainder = str(message.utterance_remainder())
        # self.speak_dialog("about", data={"result": str(gpio_request)})
        self.speak_dialog("academic")

    @intent_handler(IntentBuilder("CampusIntent").require("WhereKeyword").
                    require("CampusKeyword").optionally("ConestogaKeyword").build())
    def handle_campus_intent(self, message):
        LOG.info('Condor.ai was asked: ' + str(message.uterance()))
        self.send_MQTT('Condor.ai was asked: ' + str(message.uterance()))
        str_remainder = str(message.utterance_remainder())
        # self.speak_dialog("about", data={"result": str(gpio_request)})
        self.speak_dialog("campus")

    @intent_handler(IntentBuilder("CardIntent").require("Business").
                    require("CardKeyword").optionally("ConestogaKeyword").build())
    def handle_card_intent(self, message):
        LOG.info('Condor.ai was asked: ' + str(message.uterance()))
        self.send_MQTT('Condor.ai was asked: ' + str(message.uterance()))
        str_remainder = str(message.utterance_remainder())
        # self.speak_dialog("about", data={"result": str(gpio_request)})
        pin_index = 1
        board_pin = self.io_pins[pin_index]
        self.get_card(board_pin)
        self.send_MQTT("Condor.ai is retrieving a business card")

    def gpio_on(self, board_number, gpio_request_number):
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        GPIO.output(board_number, True)
        LOG.info('Turning On GPIO Number: ' + str(gpio_request_number))
        self.speak_dialog("on", data={"result": str(gpio_request_number)})

    def gpio_off(self, board_number, gpio_request_number):
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        GPIO.output(board_number, False)
        LOG.info('Turning Off GPIO Number: ' + str(gpio_request_number))
        self.speak_dialog("off", data={"result": str(gpio_request_number)})

    def get_card(self, program_select):
        GPIO.setup(program_select, GPIO.OUT, initial=0)
        GPIO.output(program_select, True)

    def send_MQTT(self, myMessage):
        self.client.connect("localhost", 1883, 60)
        self.client.publish("topic/mycroft.ai", myMessage);
        self.client.disconnect();

    def stop(self):
        pass


# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return CondorSkill()