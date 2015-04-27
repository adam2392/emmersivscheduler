"""
MongoEngine ORM models used for data access in the Emmersiv MongoDB database
"""

import mongoengine
from mongoengine import EmbeddedDocument, Document, EmbeddedDocumentField, DateTimeField, \
                        StringField, DictField, ListField, IntField

# connects to a Mongo DB running on the local PC on port 27017
mongoengine.connect('emmersiv')


class AppEvent(EmbeddedDocument):
    """
    Discrete application event that occurred as part of an application session
    """
    timestamp = DateTimeField(required=True)
    tag = StringField()
    eventType = StringField(required=True)
    # A custom application event data object (skeletons, questionaires, event details, etc)
    metadata = DictField(db_field='meta')


class AppSession(Document):
    """
    Top level application session object, created on app startup. Contains a list of discrete events.
    """
    startTime = DateTimeField(required=True)
    endTime = DateTimeField()
    userId = StringField(required=True)
    sessionId = StringField(required=True)
    events = ListField(EmbeddedDocumentField('AppEvent'))
    application = StringField(required=True)

    # specifies the name of the collection for these objects in the DB
    meta = {'collection': 'appsessions'}


class FileUpload(Document):
    """
    Used to keep a history of all the files uploaded to the server.
    """
    userId = StringField(required=True)
    timestamp = DateTimeField(required=True)
    fileType = StringField()
    sessionId = StringField(required=True)
    filename = StringField(required=True)
    fileSize = IntField()
    mimeType = StringField()

    # specifies the name of the collection for these objects in the DB
    meta = {'collection': 'fileuploads'}

#
# Example of how to use mongoengine
#
if __name__ == '__main__':
    # example on how to find documents
    print 'Image file uploads'
    for file in FileUpload.objects(mimeType='image/jpeg'):
        print file.timestamp, file.filename

    # example on how to find sub documents
    # filter by user ID first, then find sessions that have an event of the type 'game'
    for session in AppSession.objects(userId='Asim', events__eventType='game'):
        print 'app session: ', session.sessionId
        print 'user:', session.userId
        print 'contained events:'
        for event in session.events:
            print event.timestamp, event.eventType, event.tag
        print '===='
