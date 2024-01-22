from flask_restful import Resource, fields, marshal_with, request, reqparse, abort

from backend.api.common.roles import Role
from backend.api.common.token_manager import TokenManager, Token
from backend.api.common.ldap_manager import AuthenticationLDAP
from backend.api.common.user_manager import UserLdap


resource_field = {
    'token': fields.String
}

parser = reqparse.RequestParser()
parser.add_argument('username', type=str, required=True)
parser.add_argument('password', type=str, required=True)


class AuthOpenLDAP(Resource):

    @marshal_with(resource_field)
    def post(self):  # pass and uid (it is part of the dn) check ldap.
        """
        This function confirms the args username and password,
        then performs authentication, if authentication is successful
        token is sent user, else error 403.
        """

        args = parser.parse_args()

        user = UserLdap(username_uid=args['username'], userPassword=args['password'])
        ldap_auth = AuthenticationLDAP(user)
        response = ldap_auth.authenticate()
        if response.status.value == 1:
            abort(403, message='Invalid username or password.')

        ldap_auth.connect()

        user.dn = response.user_dn
        user.uid = response.user_id
        user.is_webadmin = ldap_auth.is_webadmin(user.dn)
        if user.is_webadmin:
            user.role = Role.WEBADMIN

        ldap_auth.close_connection()

        token = TokenManager(user=user).create_token()
        return Token(token=token), 200
