import json
from . import classifiers, stop_handlers
from .models import *
from ..settings import Default
from ..share.tools import Serialize


def parameters_for(analyzer):
    return Serialize(analyzer.DefaultParameters()).to_json()


def DefaultClassifierParameters():
    return parameters_for(getattr(classifiers, Default.classifier))


def DefaultStopLossParameters():
    return parameters_for(getattr(stop_handlers, Default.stop_loss))


@db_session
def create_user(**kwargs):
    portfolio = Portfolio(assets=Default.initial_assets)
    User(**kwargs, portfolio=portfolio)


@db_session
def create_default_operation(user):

    Operation(
        user=user,
        market=Market(),
        position=Position(),
        last_check=LastCheck(by_classifier_at=0),
        classifier=Classifier(
            name=Default.classifier, parameters=DefaultClassifierParameters()
        ),
        stop_loss=StopLoss(
            name=Default.stop_loss, parameters=DefaultStopLossParameters()
        ),
    )
