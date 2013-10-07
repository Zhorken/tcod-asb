from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound

import asb.models as models
from asb.views.redirect import attempt_redirect

@view_config(route_name='trainer_index', renderer='/indices/trainers.mako')
def TrainerIndex(context, request):
    trainers = (
        models.DBSession.query(models.Trainer)
        .order_by(models.Trainer.name)
        .all()
    )

    return {'trainers': trainers}

@view_config(route_name='trainer', renderer='/trainer.mako')
def Trainer(context, request):
    try:
        trainer = (
            models.DBSession.query(models.Trainer)
            .filter_by(identifier=request.matchdict['identifier'])
            .one()
        )
    except NoResultFound:
        attempt_redirect(request.matchdict['identifier'],
            models.Trainer, request)

    return {'trainer': trainer}