import boto3
from flask import current_app



def send_email(destination, subject, message, html):

    #Load the email client
    client = boto3.client('ses')

    if( not html ):
        html = message

    response = client.send_email( 
        Source = current_app.config['SENDER'],
        Destination = {
            'ToAddresses':destination
        },      
        Message = {
            'Subject':{
                'Data':subject,
                'Charset':current_app.config['CHARSET']
            },
            'Body':{
                'Text':{
                    'Data':message,
                    'Charset':current_app.config['CHARSET']
                },
                'Html':{
                    'Data':html,
                    'Charset':current_app.config['CHARSET']
                }
            }
        }    
    )
    
    return response
    
    
