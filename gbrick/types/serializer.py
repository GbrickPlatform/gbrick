
import json
import copy

from abc import ABC, abstractmethod
from utils.exceptions import SerializeError
from typing import List


class BaseSerializer(ABC):

    @abstractmethod
    def serialize(self, setup): raise NotImplementedError

    @abstractmethod
    def to_dict(self): raise NotImplementedError

    @abstractmethod
    def to_json(self): raise NotImplementedError


class Serializer(BaseSerializer):
    """ Serializer
    type structure serialize class
    :: transaction, block, ...
    """
    dict_slots: List[str]

    def __init__(self, *args, **kwargs):

        if kwargs:
            data_fields = tuple(self._set_fields(args, kwargs))
        else:
            data_fields = args

        if len(self.__slots__) != len(data_fields):
            raise SerializeError('Field arguments discordance: '
                                 'Expected args({}), Got args ({})'.format(
                                    len(self.__slots__), len(data_fields)))

        for fields, value in zip(self.__slots__, data_fields):
            # if type(value) is field_type:
            #     raise ValueError('{} fields set error'.format(field_name))
            setattr(self, fields, value)

    def _set_fields(self, args, kwargs):
        # kwargs is merge to args
        # TODO: kwargs merge
        add_frozen_fields = self.__slots__[len(args):]

        yield from args
        for name in add_frozen_fields:
            yield kwargs[name]

    def serialize(self, setup):
        attr = []
        for name in setup:
            _attr = getattr(self, name)
            if isinstance(_attr, int):
                attr.append(str(_attr))
            elif isinstance(_attr, bytes):
                attr.append(_attr.decode())
            elif isinstance(_attr, float):
                attr.append(str(_attr))
            elif isinstance(_attr, str):
                attr.append(_attr)
        return attr

    def to_dict(self):
        obj = {}
        for name, value in zip(self.dict_slots, self.__slots__):
            if hasattr(self, value):
                attr = getattr(self, value)

                if isinstance(attr, bytes):
                    obj[name] = attr.decode()
                else:
                    obj[name] = attr
        return obj

    def to_json(self):
        return json.dumps(self.to_dict())

    def copy(self, **kwargs):
        bind_key = set(self.__slots__).difference(
            kwargs.keys()
        )
        bind_kwargs = {
           k: copy.deepcopy(getattr(self, k))
           for k in bind_key
        }
        merge_kwargs = dict(**bind_kwargs, **kwargs)
        return type(self)(**merge_kwargs)

    def hash(self): raise NotImplementedError

