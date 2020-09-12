from decimal import Decimal

import pytest

from bitcart import errors

from ...utils import data_check

pytestmark = pytest.mark.asyncio


async def test_balance(btc_wallet):
    attrs = ["confirmed", "unconfirmed", "unmatured", "lightning"]
    balance = await btc_wallet.balance()
    for attr in attrs:
        assert balance[attr] >= 0  # NOTE: unconfirmed can be negative
        assert isinstance(balance[attr], Decimal)


async def test_history(btc_wallet):
    history = await btc_wallet.history()
    data_check(history, "summary", dict)
    data_check(history, "transactions", list, 0)


async def test_payment_request(btc_wallet):
    # request1
    request1_amount = "0.5"
    request1 = await btc_wallet.add_request(request1_amount)
    assert request1[btc_wallet.amount_field] == request1["amount_BTC"] == Decimal(request1_amount)
    # request2
    request2_amount, request2_desc = "0.6", "test description"
    request2 = await btc_wallet.add_request(request2_amount, request2_desc)
    assert request2["amount_BTC"] == Decimal(request2_amount)
    assert request2["message"] == request2_desc
    # get request2
    response2 = await btc_wallet.get_request(request2["address"])
    assert response2["amount_BTC"] == Decimal(request2_amount)
    assert response2["message"] == request2_desc
    # full data structure check
    assert (
        request1.items()
        > {
            "is_lightning": False,
            "amount_BTC": Decimal("0.5"),
            "message": "",
            "expiration": 900,
            "status": 0,
            "status_str": "Expires in 15 minutes",
            "amount_sat": 50000000,
        }.items()
    )
    data_check(request1, "timestamp", int)
    data_check(request1, "address", str)
    data_check(request1, "URI", str)


async def test_insufficient_funds_pay(btc_wallet):
    with pytest.raises(errors.NotEnoughFundsError):
        await btc_wallet.pay_to("1KQah89MJhmhxB9hRQN6DnMSkPH3RUjPev", 0.1)


async def test_fee_and_feerate(btc_wallet):  # can't set both fee and feerate
    with pytest.raises(TypeError):
        await btc_wallet.pay_to("1KQah89MJhmhxB9hRQN6DnMSkPH3RUjPev", 0.1, fee=1, feerate=1)
    with pytest.raises(TypeError):
        await btc_wallet.pay_to_many(
            [("1KQah89MJhmhxB9hRQN6DnMSkPH3RUjPev", 0.1), ("1KQah89MJhmhxB9hRQN6DnMSkPH3RUjPev", 0.1)], fee=1, feerate=1
        )
