#! /usr/bin/python
# Variations on init exchange.
# Spec: MUST respond to known feature bits as specified in [BOLT #9](09-features.md).

from lnprototest import TryAll, Connect, Disconnect, EventError, ExpectMsg, Msg, ExpectError, has_bit, bitfield, bitfield_len
import pyln.proto.message.bolt1
from fixtures import *  # noqa: F401,F403


# BOLT #1: The sending node:
# ...
# - SHOULD NOT set features greater than 13 in `globalfeatures`.
def no_gf13(event, msg, unused):
    for i in range(14, bitfield_len(msg, 'globalfeatures')):
        if has_bit(msg, 'globalfeatures', i):
            raise EventError(event, "globalfeatures bit {} set".format(i))


def no_feature(event, msg, featurebits):
    for bit in featurebits:
        if has_bit(msg, 'features', bit):
            raise EventError(event, "features set bit {} unexpected: {}".format(bit, msg))


def has_feature(event, msg, featurebits):
    for bit in featurebits:
        if not has_bit(msg, 'features', bit):
            raise EventError(event, "features set bit {} unset: {}".format(bit, msg.to_str()))


def test_init(runner, namespaceoverride):
    # We override default namespace since we only need BOLT1
    namespaceoverride(pyln.proto.message.bolt1.namespace)
    test = [Connect(connprivkey='03'),
            ExpectMsg('init'),
            Msg('init', globalfeatures='', features=''),

            # optionally disconnect that first one
            TryAll([[], Disconnect()]),

            Connect(connprivkey='02'),
            TryAll([
                # Even if we don't send anything, it should send init.
                [ExpectMsg('init')],

                # Minimal possible init message.
                # BOLT #1:
                # The sending node:
                #  - MUST send `init` as the first Lightning message for any connection.
                [ExpectMsg('init'),
                 Msg('init', globalfeatures='', features='')],

                # BOLT #1:
                # The sending node:...
                #  - SHOULD NOT set features greater than 13 in `globalfeatures`.
                [ExpectMsg('init', if_match=no_gf13),
                 # BOLT #1:
                 # The receiving node:...
                 #  - upon receiving unknown _odd_ feature bits that are non-zero:
                 #    - MUST ignore the bit.

                 # init msg with unknown odd global bit (19): no error
                 Msg('init', globalfeatures=bitfield(19), features='')],

                # Sanity check that bits 34 and 35 are not used!
                [ExpectMsg('init', if_match=no_feature, if_arg=[34, 35]),
                 # BOLT #1:
                 # The receiving node:...
                 #  - upon receiving unknown _odd_ feature bits that are non-zero:
                 #    - MUST ignore the bit.

                 # init msg with unknown odd local bit (19): no error
                 Msg('init', globalfeatures='', features=bitfield(19))],

                # BOLT #1:
                # The receiving node: ...
                #  - upon receiving unknown _even_ feature bits that are non-zero:
                #    - MUST fail the connection.
                [ExpectMsg('init'),
                 Msg('init', globalfeatures='', features=bitfield(34)),
                 ExpectError()],

                # init msg with unknown even global bit (34): you will error
                [ExpectMsg('init'),
                 Msg('init', globalfeatures=bitfield(34), features=''),
                 ExpectError()],

                # FIXME: Test based on features of runner!
            ])]

    runner.run(test)
