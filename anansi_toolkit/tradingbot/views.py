from pony.orm import db_session
import json
from . import classifiers, stop_handlers
from .models import (
    User,
    Operation,
    Market,
    LastCheck,
    Position,
    Assets,
    Classifier,
    StopLoss,
)
from ..settings import Default
from ..share.tools import Serialize


def default_parameters_for(analyzer):
    return Serialize(analyzer.DefaultParameters()).to_json()


def DefaultClassifierParameters():
    return default_parameters_for(getattr(classifiers, Default.classifier))


def DefaultStopLossParameters():
    return default_parameters_for(getattr(stop_handlers, Default.stop_loss))


@db_session
def create_user(**kwargs):
    User(**kwargs)


@db_session
def create_default_operation(user):
    Operation(
        user=user,
        market=Market(),
        position=Position(assets=Assets()),
        last_check=LastCheck(by_classifier_at=0),
        classifier=Classifier(
            name=Default.classifier, parameters=DefaultClassifierParameters()
        ),
        stop_loss=StopLoss(
            name=Default.stop_loss, parameters=DefaultStopLossParameters()
        ),
    )
