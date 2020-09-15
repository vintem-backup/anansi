import json
from . import classifiers, stop_handlers
from .models import *
from ..settings import Default


def parameter_dict_for(analyzer):
    return json.dumps(
        analyzer.DefaultParameters(), default=lambda o: o.__dict__, indent=4
    )


def DefaultClassifierParameters():
    return parameter_dict_for(getattr(classifiers, Default.classifier))


def DefaultStopLossParameters():
    return parameter_dict_for(getattr(stop_handlers, Default.stop_loss))


@db_session
def create_user(**kwargs):
    User(**kwargs)


@db_session
def create_default_operation(user):

    Operation(
        user=user,
        market=Market(),
        position=Position(),
        wallet=Wallet(),
        last_check=LastCheck(),
        classifier=Classifier(
            name=Default.classifier, parameters=DefaultClassifierParameters()
        ),
        stop_loss=StopLoss(
            name=Default.stop_loss, parameters=DefaultStopLossParameters()
        ),
    )
