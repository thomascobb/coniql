from device.channel.ca.bool import CaBool
from device.channel.ca.channel import CaChannel
from device.channel.ca.enum import CaEnum
from device.channel.ca.string import CaString
from device.devices.motor import Motor


def motor(prefix: str) -> Motor:
    return Motor(
        setpoint=CaChannel(f'{prefix}'),
        position=CaChannel(f'{prefix}.RBV'),
        stationary=CaBool(f'{prefix}.DMOV'),
        p=CaChannel(f'{prefix}.PCOF'),
        i=CaChannel(f'{prefix}.ICOF'),
        d=CaChannel(f'{prefix}.DCOF'),
        jog_positive=CaBool(f'{prefix}.TWF'),
        jog_negative=CaBool(f'{prefix}.TWR'),
        step_length=CaChannel(f'{prefix}.TWV'),
        velocity=CaChannel(f'{prefix}.VELO'),
        max_velocity=CaChannel(f'{prefix}.VMAX'),
        min=CaChannel(f'{prefix}.LLM'),
        max=CaChannel(f'{prefix}.HLM'),
        acceleration_time=CaChannel(f'{prefix}.ACCL'),
        output=CaString(f'{prefix}.OUT'),
        resolution=CaChannel(f'{prefix}.MRES'),
        offset=CaChannel(f'{prefix}.OFF'),
        units=CaString(f'{prefix}.EGU'),
        cs_port=CaEnum(f'{prefix}:CsPort', rbv_suffix='_RBV'),
        cs_axis=CaString(f'{prefix}:CsAxis', rbv_suffix='_RBV'),
    )