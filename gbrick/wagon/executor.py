
from utils.address import create_contract
from utils.config import CREATE_CONTRACT
from gbrick.validation import validate_nonce
from utils.exceptions import ValidationError
from gbrick.types.base import BaseTransaction

from gbrick.wagon.base import (
    BaseExecutor, BaseState, BaseExecuteContext
)


class Executor(BaseExecutor):

    def validate_context(self, state, context, transaction):
        if context.limited != transaction.amount_fee:
            raise ValidationError(
                "execute context limited: {}, "
                "current limited: {}".format(
                    context.limited, transaction.amount_fee
                )
            )
        if context.value != transaction.amount_value:
            raise ValidationError(
                "execute context value: {}"
                "current value: {}".format(
                    context.value, transaction.amount_value
                )
            )
        if context.txbase != transaction.address_sender:
            raise ValidationError(
                "execute context base: {}, "
                "current sender: {}".format(
                    context.nodebase, transaction.address_sender
                )
            )
        nonce = state.state_db.get_nonce(context.txbase)
        if context.nonce != nonce:
            raise ValidationError(
                "execute context nonce: {}"
                "current nonce: {}".format(
                    context.nonce, nonce
                )
            )

    def prepare_execute(self,
                        state: BaseState,
                        context: BaseExecuteContext,
                        transaction: BaseTransaction):

        self.validate_context(state, context, transaction)

        # obtain balance for used transaction
        state.state_db.compute_balance(context.txbase, -1 * context.limited)
        state.state_db.increase_nonce(context.txbase)
        context.use('execute')
        if transaction.address_recipient == CREATE_CONTRACT:
            # TODO: type contract, b''
            create_address = create_contract(context.txbase,
                                             context.nonce)
            message = {'create_address': create_address}
            code = transaction.message
            # TODO
            # transaction [message] parsing / structure /
            # data field 더 필요한가.
        else:
            # TODO: type or [gbc, gbx]
            create_address = b''
            message = transaction.message  # code method call.
            code = state.state_db.get_code(context.to)  # account[contract] get code.

        context.set_address(create_address)
        context.set_message(message)
        context.set_code(code)
        validate_nonce(context.nonce + 1,
                       state.state_db.get_nonce(context.txbase))
        context.increase_nonce()

    async def execute(self, state: BaseState, context: BaseExecuteContext):
        state.state_db.increase_nonce(context.txbase)
        if context.is_create:
            nonce = state.state_db.get_nonce(context.create_address)
            if nonce != 0:
                '''
                 receipt error = "Already contract address: {}".format(
                    self.execute_context.create_address)
                '''
                raise ValidationError(
                    "Already contract address: {}".format(
                        context.create_address
                    )
                )
            else:
                # TODO: contract set code. build to account for contract
                precompile, error = context.is_precompile()
                if precompile and error is None:
                    pass
                else:
                    raise ValidationError(
                        "contract code build failed"
                    )
            context.use('create')   # fee computation for "create" command.
        else:
            # TODO: wagon: call code, transfer value
            if context.code:
                context.use('call')  # fee computation for "call" command.
                # computation class -> byte-code execution
            else:
                state.state_db.compute_balance(context.txbase, -1 * context.value)
                state.state_db.compute_balance(context.to, context.value)
        state.state_db.compute_balance(context.txbase, context.fee_remainder)
        # todo: 잘못된 트랜잭션, 에러나는 경우 -> 해당되는 수수료 차감

    async def __call__(self,
                       state: BaseState,
                       context: BaseExecuteContext,
                       transaction: BaseTransaction):
        self.prepare_execute(state, context, transaction)
        await self.execute(state, context)

