import pbkdf2
import pyramid.httpexceptions as httpexc
import pyramid.security
from pyramid.view import view_config
import sqlalchemy as sqla
import sqlalchemy.orm
import wtforms

from asb import db
import asb.forms
import asb.tcodf

def get_user(request):
    """Get the logged-in user for a request."""

    id = pyramid.security.unauthenticated_userid(request)

    if id is None:
        return None

    try:
        user = (db.DBSession.query(db.Trainer)
            .filter_by(id=id)
            .one()
        )
    except sqla.orm.exc.NoResultFound:
        return None

    return user

def get_user_roles(userid, request):
    """Get a user's roles for Pyramid authorization."""

    try:
        user = (
            db.DBSession.query(db.Trainer)
            .filter_by(id=userid)
            .options(sqla.orm.subqueryload('roles'))
            .one()
        )
    except sqla.orm.exc.NoResultFound:
        return None

    roles = [role.identifier for role in user.roles]
    roles.append('user:{}'.format(userid))

    if user.is_validated:
        roles.append('validated')

    return roles

class UsernameField(wtforms.StringField):
    """A username field that also fetches the corresponding registered user, if
    any, from the database.
    """

    def process_formdata(self, valuelist):
        self.data, = valuelist

        try:
            trainer = (db.DBSession.query(db.Trainer)
                .filter(sqla.func.lower(db.Trainer.name) == self.data.lower())
                .filter_by(unclaimed_from_hack=False)
                .one())

            self.trainer = trainer
        except sqla.orm.exc.NoResultFound:
            self.trainer = None

class LoginForm(asb.forms.CSRFTokenForm):
    """A login form, used both at the top of every page and on /login."""

    username = UsernameField('Username', [asb.forms.name_validator])
    password = wtforms.PasswordField('Password')
    log_in = wtforms.SubmitField('Log in')

    # n.b. we don't want the username and password fields to present separate
    # errors to the user because that might look like a security risk to the
    # average person (even though there's a public userlist)
    def validate_username(form, field):
        """Make sure we actually found a current user for this username."""

        if field.trainer is None:
            raise wtforms.validators.ValidationError

    def validate_password(form, field):
        """If we got a valid user, check their password against the password
        we got.
        """

        trainer = form.username.trainer

        if trainer is None or trainer.unclaimed_from_hack:
            # The username field will raise an error; there's no sensible
            # second error to be raised here
            return None

        if not trainer.check_password(field.data):
            raise wtforms.validators.ValidationError

class RegistrationForm(asb.forms.CSRFTokenForm):
    """A registration form."""

    username = UsernameField('TCoD forum username',
        [wtforms.validators.InputRequired(), asb.forms.name_validator])
    password = wtforms.PasswordField('Choose a password',
        [wtforms.validators.InputRequired("Your password can't be empty")])
    password_confirm = wtforms.PasswordField('Confirm')
    email = wtforms.StringField('Email (optional)')
    submit = wtforms.SubmitField('Register')

    def validate_password_confirm(form, field):
        """Make sure the passwords match."""

        if field.data != form.password.data:
            raise wtforms.validators.ValidationError("Passwords don't match")

    def validate_username(form, field):
        """Make sure they're not trying to register as an already-registered
        trainer.
        """

        if field.trainer is not None:
            raise wtforms.validators.ValidationError(
                'The username {0} has already been registered.  If someone '
                'else is using your username, contact an ASB mod.'
                .format(field.data)
            )

class UserLinkField(wtforms.StringField):
    """A field for a forum profile link that also retrieves profile info."""

    tcodf_user_id = None
    preexisting_trainer = None
    tcodf_user_info = None

    def process_formdata(self, valuelist):
        """Process form data, and also retreive profile info."""

        [self.data] = valuelist
        self.tcodf_user_id = asb.tcodf.user_id(self.data)
        self.tcodf_user_info = asb.tcodf.user_info(self.tcodf_user_id)

        # See if there's already a trainer with this TCoDf ID
        try:
            self.preexisting_trainer = (
                db.DBSession.query(db.Trainer)
                .filter_by(tcodf_user_id=self.tcodf_user_id)
                .one()
            )
        except sqla.orm.exc.NoResultFound:
            pass

    def pre_validate(self, form):
        """Make sure nobody else has already validated using this forum
        account.

        Yes, we also have to check that the right profile link is in the right
        place, but we do that elsewhere to avoid having to pass the user id all
        over.
        """

        return

        if (self.preexisting_trainer is not None and not
          self.preexisting_trainer.unclaimed_from_hack):
            raise wtforms.validators.ValidationError('That forum account is '
                'already associated with an ASB profile')

class ValidationForm(asb.forms.CSRFTokenForm):
    """An account validation form."""

    profile_link = UserLinkField(validators=[wtforms.validators.Required()])
    submit = wtforms.SubmitField('Validate')

@view_config(route_name='register', renderer='/register.mako',
  request_method='GET')
def register(context, request):
    """Return a blank registration form."""

    return {'form': RegistrationForm(csrf_context=request.session)}

@view_config(route_name='register', renderer='/register.mako',
  request_method='POST')
def register_commit(context, request):
    """Process a registration form.  Send the user back to the form if there
    are any errors; create their account otherwise.
    """

    form = RegistrationForm(request.POST, csrf_context=request.session)

    if not form.validate():
        return {'form': form}

    # Create a new user
    username = form.username.data
    identifier = 'temp-{0}'.format(username)
    user = db.Trainer(name=username, identifier=identifier)

    db.DBSession.add(user)
    db.DBSession.flush()  # Set their ID

    user.set_password(form.password.data)
    user.update_identifier()

    # Log them in
    headers = pyramid.security.remember(request, user.id)

    return httpexc.HTTPSeeOther('/validate', headers=headers)

@view_config(route_name='validate', renderer='/validate.mako',
  permission='account.validate', request_method='GET')
def validate_page(context, request):
    """The validation page."""

    return {'form': ValidationForm(csrf_context=request.session)}

@view_config(route_name='validate', renderer='/validate.mako',
  permission='account.validate', request_method='POST')
def validate(context, request):
    """Validate a user, and give them back their old profile if applicable."""

    form = ValidationForm(request.POST, csrf_context=request.session)
    return_dict = {'form': form}

    if not form.validate():
        return return_dict

    trainer = request.user
    old_trainer = form.profile_link.preexisting_trainer
    info = form.profile_link.tcodf_user_info

    # Check the profile link, but be lenient about the slug
    link = info['profile_link']

    if link is None:
        form.profile_link.errors.append("Couldn't find an ASB profile link on "
            "that forum profile")
        return return_dict
    else:
        path, sep, slug = info['profile_link'].path.partition('-')

        if path != '/trainers/{}'.format(trainer.id):
            form.profile_link.errors.append('Found an ASB link on that forum '
                "profile, but it's the wrong link")
            return return_dict

    if old_trainer:
        # We found an old profile from the vB hack — replace this user with it
        id = trainer.id
        identifier = trainer.identifier
        old_trainer.password_hash = trainer.password_hash
        old_trainer.name = trainer.name

        db.DBSession.delete(trainer)
        db.DBSession.flush()

        trainer = old_trainer
        trainer.id = id
        trainer.identifier = identifier

        # Update all their Pokémon's IDs
        for pokemon in trainer.pokemon:
            pokemon.id = db.DBSession.execute(asb.db.Pokemon.pokemon_id_seq)
            pokemon.update_identifier()

    username = info['username']

    if trainer.name != username:
        request.session.flash('Your username has been updated to match your '
            'forum profile.')
        trainer.name = username
        trainer.update_identifier()

    trainer.tcodf_user_id = form.profile_link.tcodf_user_id
    trainer.is_validated = True

    return httpexc.HTTPSeeOther('/')

@view_config(route_name='login', renderer='/login.mako',
  request_method='GET')
def login_page(context, request):
    """Return a blank login form in the unlikely event that anyone ever GETs
    /login.
    """

    return {'form': LoginForm(csrf_context=request.session)}

@view_config(route_name='login', renderer='/login.mako',
  request_method='POST')
def login(context, request):
    """Process a login form."""

    form = LoginForm(request.POST, csrf_context=request.session)

    if not form.validate():
        return {'form': form}

    headers = pyramid.security.remember(request, form.username.trainer.id)

    return httpexc.HTTPSeeOther('/', headers=headers)

@view_config(route_name='logout')
def logout(context, request):
    if request.params['csrf_token'] == request.session.get_csrf_token():
        headers = pyramid.security.forget(request)
        return httpexc.HTTPSeeOther('/', headers=headers)
    else:
        request.session.flash('Invalid CSRF token; the logout link probably '
            'expired.  Try again.')

        return httpexc.HTTPSeeOther('/')
