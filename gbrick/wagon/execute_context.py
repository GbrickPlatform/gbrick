
import json
from utils.exceptions import FeeLimitedError
from utils.config import UNIT, FEE_EXECUTE, FEE_CREATE, FEE_CALL
from gbrick.wagon.base import BaseExecuteContext
from gbrick.validation import validate_code
from utils.config import CREATE_CONTRACT
from utils.exceptions import ValidationError


class Fee:
    execute = int(UNIT * FEE_EXECUTE)
    create = int(UNIT * FEE_CREATE)
    call = int(UNIT * FEE_CALL)


class ExecuteContext(BaseExecuteContext):
    """ context are use on executor
    context from transaction and
    complete executed was write to receipt on context
    """
    _ratio = Fee()

    @property
    def is_create(self):
        return self.to == CREATE_CONTRACT

    @property
    def is_error(self):
        return self._error is not ''

    @property
    def create_address(self):
        return self._create_address

    @property
    def txbase(self):
        return self._tx_base

    @property
    def limited(self):
        return self._limited

    @property
    def type(self):
        return self._type

    @property
    def nonce(self):
        return self._nonce

    @property
    def ratio(self):
        return self._ratio

    @property
    def code(self):
        return None

    @property
    def message(self):
        # -> json?
        return self._message

    @property
    def paid(self):
        return self._fee

    @property
    def fee_remainder(self):
        return self.limited - self._fee

    @property
    def error(self):
        return self._error

    def increase_nonce(self):
        self._nonce += 1

    def use(self, cmd):
        consume = getattr(self.ratio, cmd)
        self._fee += consume
        if self._fee > self.limited:
            raise FeeLimitedError(
                "fee limited: {}, "
                "expected consume fee: {}".format(
                    self.limited, self._fee
                )
            )

    def set_code(self, code):
        code = validate_code(code)
        self._code = code

    def set_message(self, message):
        try:
            if message != '' and isinstance(message, str):
                message = json.loads(message)
            self._message = dict(message)
        except Exception as e:
            raise ValidationError("message unexpected type, {}".format(type(message)))

    def set_address(self, create_address):
        self._create_address = create_address

    def set_error(self, err):
        self._error = str(err)

    def is_precompile(self):
        try:
            pre = self._code.get('is_precompiled')
            basic = self._code.get('codes')
            self._state['is_precompiled'] = pre
            self._state['codes'] = basic
            self._code = self._state['codes'].encode()
            return True, None
        except Exception as e:
            str(e)
            return None, None





