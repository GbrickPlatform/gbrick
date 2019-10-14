
from gbrick.types.base import (
    BaseAccount, BaseRep
)


class Account(BaseAccount):

    @property
    def base(self):
        return self.address_account

    @property
    def hash(self):
        # TODO
        return


class Rep(BaseRep):

    @property
    def hash(self):
        setup = self.__slots__
        attr = self.serialize(setup)
        return attr



