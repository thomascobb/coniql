import asyncio
import base64
import datetime
import json
from enum import Enum
from typing import List, Optional, Sequence

import numpy as np
import strawberry

from coniql.caplugin import CAPlugin
from coniql.plugin import PluginStore
from coniql.pvaplugin import PVAPlugin
from coniql.simplugin import SimPlugin

store_global = PluginStore()
store_global.add_plugin("ssim", SimPlugin())
store_global.add_plugin("pva", PVAPlugin())
store_global.add_plugin("ca", CAPlugin(), set_default=True)


@strawberry.enum
class NumberType(Enum):
    """
    Numeric type for arrays of numbers
    """

    INT8 = "INT8"
    UINT8 = "UINT8"
    INT16 = "INT16"
    UINT16 = "UINT16"
    INT32 = "INT32"
    UINT32 = "UINT32"
    INT64 = "INT64"
    UINT64 = "UINT64"
    FLOAT32 = "FLOAT32"
    FLOAT64 = "FLOAT64"


@strawberry.enum
class ChannelRole(Enum):
    """
    What access role has the Channel
    """

    RO = "RO"
    WO = "WO"
    RW = "RW"


@strawberry.enum
class Widget(Enum):
    """
    Widget that should be used to display a Channel
    """

    # Editable text input
    TEXTINPUT = "TEXTINPUT"
    # Read-only text display
    TEXTUPDATE = "TEXTUPDATE"
    # Multiline read-only text display
    MULTILINETEXTUPDATE = "MULTILINETEXTUPDATE"
    # Read-only LED indicator
    LED = "LED"
    # Editable combo-box style menu for selecting between fixed choices
    COMBO = "COMBO"
    # Editable check box
    CHECKBOX = "CHECKBOX"
    # Editable progress type bar
    BAR = "BAR"
    # Clickable button to send default value to Channel
    BUTTON = "BUTTON"
    # X-axis for lines on a graph. Only valid within a Group with widget Plot
    PLOTX = "PLOTX"
    # Y-axis for a line on a graph. Only valid within a Group with widget Plot
    PLOTY = "PLOTY"


@strawberry.enum
class DisplayForm(Enum):
    """
    Instructions for how a number should be formatted for display
    """

    # Use the default representation from value
    DEFAULT = "DEFAULT"
    # Force string representation, most useful for array of bytes
    STRING = "STRING"
    # Binary, precision determines number of binary digits
    BINARY = "BINARY"
    # Decimal, precision determines number of digits after decimal point
    DECIMAL = "DECIMAL"
    # Hexadecimal, precision determines number of hex digits
    HEX = "HEX"
    # Exponential, precision determines number of digits after decimal point
    EXPONENTIAL = "EXPONENTIAL"
    # Exponential where exponent is multiple of 3, precision determines number
    # of digits after decimal point
    ENGINEERING = "ENGINEERING"


@strawberry.type
class Range:
    """
    A range of numbers. Null in either field means unbounded in that direction.
    A value is in range if min <= value <= max
    """

    # The minimum number that is in this range
    min: float
    # The maximum that is in this range
    max: float


@strawberry.enum
class ChannelQuality(Enum):
    """
    Indication of how the current value of a Channel should be interpreted
    """

    # Value is known, valid, nothing is wrong
    VALID = "VALID"
    # Value is known, valid, but is in the range generating a warning
    WARNING = "WARNING"
    # Value is known, valid, but is in the range generating an alarm condition
    ALARM = "ALARM"
    # Value is known, but not valid, e.g. a RW before its first put
    INVALID = "INVALID"
    # The value is unknown, for instance because the channel is disconnected
    UNDEFINED = "UNDEFINED"
    # The Channel is currently in the process of being changed
    CHANGING = "CHANGING"


@strawberry.type
class Base64Array:
    """
    Base-64 encodable numeric array
    """

    # Type of the native array
    numberType: NumberType
    # Base64 encoded version of the array
    base64: str


@strawberry.type
class ChannelValue:
    """
    Value that can be formatted in a number of ways
    """

    @strawberry.field
    async def float(root) -> Optional[float]:
        """The current value formatted as a Float, Null if not expressable"""
        return root.formatter.to_float(root.value)

    @strawberry.field
    async def string(root, units: bool = False) -> Optional[str]:
        """The current value formatted as a string"""
        if units:
            return root.formatter.to_string_with_units(root.value)
        else:
            return root.formatter.to_string(root.value)

    @strawberry.field
    async def base64Array(root, length: int = 0) -> Optional[Base64Array]:
        """Array of base64 encoded numbers, Null if not expressable"""
        return root.formatter.to_base64_array(root.value, length)

    @strawberry.field
    async def stringArray(root, length: int = 0) -> Optional[List[str]]:
        """Array of strings, Null if not expressable"""
        return root.formatter.to_string_array(root.value, length)


@strawberry.type
class ChannelStatus:
    """
    The current status of a Channel, including alarm and connection status
    """

    # Of what quality is the current Channel value
    quality: ChannelQuality
    # Free form text describing the current status
    message: str
    # Whether the Channel will currently accept mutations
    mutable: bool


@strawberry.type
class ChannelTime:
    """
    Timestamp indicating when a value was last updated
    """

    # Floating point number of seconds since Jan 1, 1970 00:00:00 UTC
    seconds: float
    # A more accurate version of the nanoseconds part of the seconds field
    nanoseconds: int
    # An integer value whose interpretation is deliberately undefined
    userTag: int

    @strawberry.field
    async def datetime(root) -> datetime.datetime:
        """The timestamp as a datetime object"""
        return datetime.datetime.fromtimestamp(root.seconds)


@strawberry.type
class ChannelDisplay:
    # A human readable possibly multi-line description for a tooltip
    description: str
    # What access role does the Channel have
    role: ChannelRole
    # Default widget to display this Channel
    widget: Optional[Widget]
    # If numeric, the range the put value should be within
    controlRange: Optional[Range]
    # If numeric, the range the current value should be within
    displayRange: Optional[Range]
    # If numeric, the range outside of which an alarm will be produced
    alarmRange: Optional[Range]
    # If numeric, the range outside of which a warning will be produced
    warningRange: Optional[Range]
    # If numeric, the physical units for the value field
    units: Optional[str]
    # If numeric, the number of decimal places to display
    precision: Optional[int]
    # If numeric, how should value be displayed
    form: Optional[DisplayForm]
    # If given, the value should be one of these choices
    choices: Optional[List[str]]


@strawberry.type
class Channel:
    """
    A single value with associated time, status and metadata. These values
    can be Null so that in a subscription they are only updated on change
    """

    # ID that uniquely defines this Channel, normally a PV
    id: strawberry.ID

    @strawberry.field
    async def value(root) -> Optional[ChannelValue]:
        """The current value of this channel"""
        channel = await root.get_channel()
        return channel.get_value()

    @strawberry.field
    async def time(root) -> Optional[ChannelTime]:
        """When was the value last updated"""
        channel = await root.get_channel()
        return channel.get_time()

    @strawberry.field
    async def status(root) -> Optional[ChannelStatus]:
        """Status of the connection, whether is is mutable, and alarm info"""
        channel = await root.get_channel()
        return channel.get_status()

    @strawberry.field
    async def display(root) -> Optional[ChannelDisplay]:
        """How should the Channel be displayed"""
        channel = await root.get_channel()
        return channel.get_display()


class DeferredChannel:
    id: str
    lock: asyncio.Lock
    channel: Optional[Channel] = None

    async def populate_channel(self) -> Channel:
        raise NotImplementedError(self)

    async def get_channel(self) -> Channel:
        if self.channel is None:
            async with self.lock:
                # If channel is still None we should make it
                if self.channel is None:
                    self.channel = await self.populate_channel()
        assert self.channel
        return self.channel


class GetChannel(DeferredChannel):
    def __init__(self, channel_id: str, timeout: float, store: PluginStore):
        self.plugin, self.id = store.plugin_config_id(channel_id)
        # Remove the transport prefix from the read pv
        self.pv = store.transport_pv(channel_id)[1]
        self.timeout = timeout
        self.lock = asyncio.Lock()

    async def populate_channel(self) -> Channel:
        channel = await self.plugin.get_channel(self.pv, self.timeout)
        return channel


class SubscribeChannel(DeferredChannel):
    def __init__(self, channel_id: str, channel: Channel):
        self.id = channel_id
        self.channel = channel


@strawberry.type
class Query:
    @strawberry.field
    def getChannel(self, id: strawberry.ID, timeout: float = 5.0) -> Channel:
        """Get the current value of a Channel"""
        return GetChannel(id, timeout, store_global)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def subscribeChannel(self, id: strawberry.ID) -> Channel:
        """Subscribe to changes in top level fields of Channel,
        if they haven't changed they will be Null"""
        store: PluginStore = store_global
        plugin, channel_id = store.plugin_config_id(id)
        # Remove the transport prefix from the read pv
        pv = store.transport_pv(id)[1]
        async for channel in plugin.subscribe_channel(pv):
            yield SubscribeChannel(channel_id, channel)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def putChannels(
        self,
        ids: List[strawberry.ID],
        values: List[str],
        timeout: float = 5.0,
    ) -> Sequence[Channel]:
        """Put a list of values to a list of Channels"""
        store: PluginStore = store_global
        pvs = []
        plugins = set()
        put_values = values
        for channel_id in ids:
            plugin, channel_id = store.plugin_config_id(channel_id)
            pv = channel_id
            assert pv, f"{channel_id} is configured read-only"
            plugins.add(plugin)
            pvs.append(store.transport_pv(pv)[1])
        results = []
        for value in put_values:
            if value[:1] in "[{":
                # need to json decode
                value = json.loads(value)
                if isinstance(value, dict):
                    # decode base64 array
                    dtype = np.dtype(value["numberType"].lower())
                    value_b = base64.b64decode(value["base64"])
                    # https://stackoverflow.com/a/6485943
                    value = np.frombuffer(value_b, dtype=dtype)
            results.append(value)
        assert len(results) == len(pvs), "Mismatch in ids and values length"
        assert (
            len(plugins) == 1
        ), "Can only put to pvs with the same transport, not %s" % [
            p.transport for p in plugins
        ]
        await plugins.pop().put_channels(pvs, results, timeout)
        channels = [GetChannel(channel_id, timeout, store) for channel_id in ids]
        return channels
