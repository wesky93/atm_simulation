class ATMError(Exception):
    pass

class BankError(ATMError):
    pass

class DeviceError(ATMError):
    pass

class InvalidRequest(ATMError):
    pass

class UnSuportedCard(BankError):
    pass

class InvalidPinNumber(BankError):
    pass

class InvalidAccount(BankError):
    pass

class NotEnoughMoney(DeviceError):
    pass

class CardEjectFail(DeviceError):
    pass