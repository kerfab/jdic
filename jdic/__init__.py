""" Loads the relevant Jdic features """
#pylint: disable=redefined-builtin

from .jdic import \
    Jdic, \
    JdicMapping, \
    JdicSequence, \
    MatchResult, \
    jdic_create as jdic, \
    jdic_enumerate as enumerate
from . import settings
