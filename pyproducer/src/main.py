# -*- coding: utf-8 -*-

import datetime
import logging
import json
import argparse


if __name__ == "__main__":

	# Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-stdout", "--stdout", action="store_true", default=False, help="Increase output verbosity")
    parser.add_argument("-configfile", "--configfile", required=True, help="Path to the yaml configfile")
    args = parser.parse_args()

    # Load the yaml configuration

    # Build logger
    # TODO

    # Restore RabbitMQ config from the yaml config
    # TODO

    # Produce/Consume
    # TODO
    print("hello world")
