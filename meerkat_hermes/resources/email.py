"""
This resource provides a simple means of sending a given e-mail message to given e-mail addresses.
"""
from flask_restful import Resource, reqparse
import uuid, boto3, uuid, json
from flask import current_app, Response
import meerkat_hermes.util as util
from meerkat_hermes.authentication import require_api_key


#This simple Emailer resource has just one method, which sends a given email message.
class Email(Resource):

    #Require authentication
    decorators = [require_api_key]

    def __init__(self):
        #Load the database and tables, upon object creation. 
        db = boto3.resource('dynamodb')
        self.subscribers = db.Table(current_app.config['SUBSCRIBERS'])

    def put(self):
        """
        Send an email with Amazon SES. 
        First parse the given arguments to check it is a valid email.
        !!!Remember that whilst still in AWS "Sandbox" we can only send to verified emails.

        PUT args:
            'subject'* - The e-mail subject (String)
            'message'* - The e-mail message (String)
            'email' - The destination address/es for the e-mail (String)
            'subscriber_id' - The destination subscriber/s for the e-mail (String)
            'html' - The html version of the message, will default to the same as 'message' (String)
            'from' - The sender's address. Defaults to the config value SENDER. (String)

        Returns:
            The amazon SES response.
        """

        current_app.logger.warning('Called email resource')

        #Define an argument parser for creating a valid email message.
        parser = reqparse.RequestParser()
        parser.add_argument('subject', required=True, type=str, help='The email subject')
        parser.add_argument('message', required=True, type=str, help='The message to be sent')
        parser.add_argument('email', required=False, action='append', type=str, 
                            help='The destination address')
        parser.add_argument('subscriber_id', required=False, action='append', type=str, 
                            help='The destination subscriber id')
        parser.add_argument('html', required=False, type=str, 
                            help='If applicable, the message in html')
        parser.add_argument('from', required=False, type=str, 
                            help='The address from which to send the message')
        args = parser.parse_args()

        current_app.logger.warning( 'Args are: ' + str(args) )

        #If no email is given, look at the subscriber ids and find their emails. 
        if args['email'] is None:
            #If the caller has made a mistake and not provided any destination, throw an error.
            if args['subscriber_id'] is None:
                return Response( "{'message':'404 Bad Request: No destination specified.'}",
                                 status=404,
                                 mimetype='application/json' )
            else:
                args['email'] = []
                for subscriber_id in args['subscriber_id']: 
                    response = self.subscribers.get_item(
                        Key={
                           'id':subscriber_id
                        }
                    )
                    args['email'].append( response['Item']['email'] )   

        #Set the from field to the config SENDER value if no from field is supplied.
        if not args['from']: 
            args['from'] = current_app.config['SENDER']

        response = util.send_email( 
            args['email'], 
            args['subject'], 
            args['message'], 
            args['html'],
            sender=args['from']
        )

        current_app.logger.warning('Sent email: ' + str(response) )
        message_id = 'G'+uuid.uuid4().hex

        util.log_message( message_id, {
            'destination': args['email'], 
            'medium': ['email'], 
            'time': util.get_date(),
            'message': args['message']
        })

        response['log_id'] = message_id
        
        return Response( json.dumps( response ), 
                         status=response['ResponseMetadata']['HTTPStatusCode'],
                         mimetype='application/json' )
