from os.path import dirname
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler, intent_file_handler
from mycroft.util.log import getLogger
from mycroft.util.log import LOG

from pylogix import PLC
from time import sleep
import string
import random
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
        self.broker_address = "192.168.0.43"
        self.settings["broker_address"] = self.broker_address
        self.broker_port = 1884
        self.settings["broker_port"] = self.broker_port
        self.settings["plc_address"] = "192.168.0.210"
        self.plcOutTagName = "StartRobot"
        self.settings["plc_out_tag_name"] = self.plcOutTagName
        self.plcInTagName = "RobotStarted"
        self.settings["plc_in_tag_name"] = self.plcInTagName
        self.comm = PLC()
        self._is_setup = False
        self.io_pins = []

    # This method loads the files needed for the skill's functioning, and
    # creates and registers each intent that the skill uses
    def initialize(self):
        self.io_pins = [3, 5, 7, 29, 31, 26, 24, 21, 19, 23, 32, 33, 8, 10, 36, 11, 12, 35, 38, 40, 15, 16, 18, 22, 37, 13]
        GPIO.setmode(GPIO.BOARD)
        self.load_data_files(dirname(__file__))
        #  Check and then monitor for credential changes
        self.settings.set_changed_callback(self.on_websettings_changed)
        self.on_websettings_changed()

    def on_websettings_changed(self):  # called when updating mycroft home page
        if not self._is_setup:
            self.broker_address = self.settings.get("broker_address", "192.168.0.43")
            self.broker_port = self.settings.get("broker_port", 1884)
            self.comm.IPAddress = self.settings.get("plc_address", "192.168.0.210")  # PLC Address
            self.plcOutTagName = self.settings.get("plc_out_tag_name", "StartRobot")
            self.plcInTagName = self.settings.get("plc_in_tag_name", "RobotStarted")
            self._is_setup = True

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

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
                self.speak_dialog("error", data={"result": str(gpio_request)}, wait=True)
        else:
            self.speak('No GPIO Pin was specified')

    @intent_handler(IntentBuilder("WikiIntent").require("TellKeyword").
                    require("AboutKeyword").require("ConestogaKeyword").build())
    def handle_wiki_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        self.send_MQTT("topic/mycroft.ai", 'Condor.ai was asked: ' + message.data.get('utterance'))
        str_remainder = str(message.utterance_remainder())
        self.speak_dialog("about", wait=True)
        self.card_conversation()

    @intent_handler(IntentBuilder("AcademicIntent").require("WhatKeyword").
                    require("AcademicKeyword").optionally("ConestogaKeyword").build())
    def handle_academic_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        self.send_MQTT("topic/mycroft.ai", 'Condor.ai was asked: ' + message.data.get('utterance'))
        str_remainder = str(message.utterance_remainder())
        self.speak_dialog("academic1", wait=True)
        self.speak_dialog("academic2", wait=True)
        self.card_conversation()

    # @intent_handler(IntentBuilder("CampusIntent").require("WhereKeyword").
    #                 require("CampusKeyword").optionally("ConestogaKeyword").build())
    @intent_handler(IntentBuilder("CampusIntent").require("WhereKeyword").
                    optionally("CampusKeyword").require("ConestogaKeyword").build())
    def handle_campus_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        self.send_MQTT("topic/mycroft.ai", 'Condor.ai was asked: ' + message.data.get('utterance'))
        str_remainder = str(message.utterance_remainder())
        self.speak_dialog("campus_intro", wait=True)
        self.speak_dialog("campus", wait=True)
        self.card_conversation()

    @intent_handler(IntentBuilder("SetStackLightIntent").require("SetKeyword").
                    require("StackLightKeyword").require("ColorKeyword").build())
    def handle_set_stack_light_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        color_kw = message.data.get("ColorKeyword")
        self.send_MQTT("Arcx/SL", str(color_kw))
        self.speak_dialog("set_stacklight", data={"result": str(color_kw)}, wait=True)

    @intent_handler(IntentBuilder("RobotStartIntent").require("BusinessKeyword").
                    require("CardKeyword").optionally("ConestogaKeyword").build())
    def handle_robot_start_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        self.send_MQTT("topic/mycroft.ai", 'Condor.ai was asked: ' + message.data.get('utterance'))
        str_remainder = str(message.utterance_remainder())
        self.send_MQTT("topic/mycroft.ai", "Condor.ai is retrieving a business card")
        self.start_robot()

    @intent_handler(IntentBuilder("CardConversationIntent").require("BusinessCardContextKeyword").
                    one_of('YesKeyword', 'NoKeyword').build())
    def handle_card_conversation_intent(self, message):
        LOG.info('Condor.ai was asked: ' + message.data.get('utterance'))
        self.send_MQTT("topic/mycroft.ai", 'Condor.ai was asked: ' + message.data.get('utterance'))
        str_remainder = str(message.utterance_remainder())
        self.set_context('BusinessCardContextKeyword', '')
        if "YesKeyword" in message.data:
            self.send_MQTT("topic/mycroft.ai", "Condor.ai is retrieving a business card")
            self.start_robot()
        else:
            self.speak_dialog("no_card", wait=False)

    def card_conversation(self):
        low_number = 1
        high_number = 5
        my_number = random.randint(low_number, high_number)
        LOG.info('Card Request Context ID: ' + str(my_number))
        if my_number == 5:
            self.set_context('BusinessCardContextKeyword', 'SetBusinessCardContext')
            self.speak_dialog("ask_card", wait=True, expect_response=True)

    def gpio_on(self, board_number, gpio_request_number):
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        GPIO.output(board_number, True)
        LOG.info('Turning On GPIO Number: ' + str(gpio_request_number))
        self.speak_dialog("on", data={"result": str(gpio_request_number)}, wait=True)

    def gpio_off(self, board_number, gpio_request_number):
        GPIO.setup(board_number, GPIO.OUT, initial=0)
        GPIO.output(board_number, False)
        LOG.info('Turning Off GPIO Number: ' + str(gpio_request_number))
        self.speak_dialog("off", data={"result": str(gpio_request_number)}, wait=True)

    def get_card(self, program_select):
        GPIO.setup(program_select, GPIO.OUT, initial=0)
        GPIO.output(program_select, True)

    def send_MQTT(self, myTopic, myMessage):
        self.client = mqtt.Client(self.id_generator())  # create new instance
        self.client.connect(self.broker_address, self.broker_port)  # connect to broker
        self.client.publish(myTopic, myMessage)  # publish

    def start_robot(self):
        self.write_plc("StartRobot", 1)
        LOG.info('PLC Output Should be On')
        self.speak_dialog("retrieve_card", wait=False)
        sleep(1)
        self.write_plc(self.plcOutTagName, 0)
        LOG.info('PLC Output Should be Off')
        inTag = self.comm.Read(self.plcInTagName)
        while inTag.Value == 0:
            inTag = self.comm.Read(self.plcInTagName)
            LOG.info('Checking Robot Complete Status: ' + str(inTag.Value))
            if inTag.Value == 1:
                self.speak_dialog("card_delivered", wait=False)
            else:
                sleep(0.5)

    def write_plc(self, myTagName, myTagValue):
        self.comm.Write(myTagName, myTagValue)
        self.comm.Close()

    def stop(self):
        pass


# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return CondorSkill()
