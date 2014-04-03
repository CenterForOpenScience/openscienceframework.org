import tweepy
from tweepy import Cursor
import httplib as http
import os
import json
import ctypes
from framework import request, redirect, status
from framework.sessions import session#, get_session, set_session, create_session
from framework.exceptions import HTTPError
from website import models
from website.project.decorators import must_have_addon,must_have_permission
from website.project.decorators import must_be_contributor_or_public
from framework.status import push_status_message
from website.addons.twitter.tests.utils import send_tweet
from framework.auth import get_current_user
from website import settings
from website.addons.base import AddonUserSettingsBase, AddonNodeSettingsBase
from website.addons.base import AddonError
from framework.status import push_status_message
from website.addons.twitter import AddonTwitterNodeSettings

CONSUMER_KEY = 'rohTTQSPWzgIXWw0g5dw'
CONSUMER_SECRET = '7pmpjEtvoGjnSNCN2GlULrV104uVQQhg60Da7MEEy0'


def oauth_start(*args, **kwargs):
    """Gets request token from twitter to create OAuthHandler instance

        :param None

        :return: redirects user to twitter's authentication page
        """

#Build OAuthHandler and set redirect url
    pid = kwargs.get('pid')
    callback_url = 'http://127.0.0.1:5000/api/v1/project/'+pid+'/twitter/user_auth'
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url, secure=True)

    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError as e:
        print 'Error! Failed to get request token.'
#Store request  token data in session variable
    node = models.Node.load(kwargs['pid'])
    twitter = node.get_addon('twitter')
    twitter.request_token_key = auth.request_token.key
    twitter.request_token_secret = auth.request_token.secret
    twitter.save()

    return redirect(redirect_url)

def username(*args, **kwargs):

    """Exchange request token for access token

        :param message: None

        :return: Redirects user to add-on settings page
        """

#Rebuild OAuthHandler

    pid = kwargs.get('pid')
    node = models.Node.load(kwargs['pid'])
    twitter = node.get_addon('twitter')
    callback_url = 'http://127.0.0.1:5000/api/v1/project/'+pid+'/twitter/user_auth'
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url, secure=True)

#Use request token and verifier to get access token
    auth.set_request_token(twitter.request_token_key, twitter.request_token_secret)

    verifier = request.args.get('oauth_verifier')
    session.data['verifier'] = request.args.get('oauth_verifier')

    try:
      auth.get_access_token(verifier = verifier)
    except tweepy.TweepError as e:
            raise HTTPError(400, data={'message_long':'Please try again.', 'message_short':'Twitter Error!'})

#Build access token
    auth.set_access_token(auth.access_token.key, auth.access_token.secret)

    #save to node settings model here, instead of session
   # session.data['access_token_key'] = auth.access_token.key
    #session.data['access_token_secret'] = auth.access_token.secret
    #session.save()

#Build tweepy object
    api = tweepy.API(auth)

#Build twitter add-on object, which is attached to the node

    twitter.oauth_key = auth.access_token.key
    twitter.oauth_secret = auth.access_token.secret
    twitter.user_name = api.me().screen_name
    twitter.save()
    return redirect(os.path.join(node.url, 'settings'))
    return redirect('/settings/')

def twitter_oauth():
    return {'foo':'bar'}


@must_be_contributor_or_public
@must_have_addon('twitter', 'node')
def twitter_widget(*args, **kwargs):
    """Passes twitter user data to twitter_widget.mako

        :param message: None

        :return: None
        """
    #Build OAuthHandler


    node = kwargs.get('node') or kwargs.get('project')
    twitter = kwargs.get('node_addon')
    config = node.get_addon('twitter')

    pid = kwargs.get('pid')

    if config.oauth_key:
        callback_url = 'http://127.0.0.1:5000/api/v1/project/'+pid+'/twitter/user_auth'
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url, secure=True)

        #Rebuild access token and tweepy object

        auth.set_access_token(config.oauth_key, config.oauth_secret)
        try:
            api = tweepy.API(auth)
            screen_name = api.me().screen_name

        #if user is not authorized, clear out node settings
        #TODO: decide which node settings will persist
        except tweepy.TweepError as e:
            raise HTTPError(400, data={'message_long':'Your authentication token has expired.  Visit the settings page to re-authenticate.', 'message_short':'Twitter Error'})
            screen_name = None
            twitter.log_messages = {}
            twitter.log_actions ={}
            twitter.oauth_key = None
            twitter.oauth_secret = None
            twitter.user_name = None
            twitter.save()
    else:
        screen_name = None

    #Storing variables
   # twitter = kwargs['node_addon']
    if twitter:

        if (config.displayed_tweets == None):
            config.displayed_tweets = 0

        rv = {
            'complete': True,
            'user_name': screen_name,
            'displayed_tweets': config.displayed_tweets,

        }
        rv.update(twitter.config.to_json())
        return rv
    raise HTTPError(http.NOT_FOUND)



#TODO: will node settings persist?
@must_be_contributor_or_public
@must_have_addon('twitter', 'node')
def twitter_oauth_delete_node(*args, **kwargs):
     """Removes OAuth info from twitter add-on node

        :param None

        :return: None
        """

#Get add-on object




     twitter = kwargs['node_addon']

#Zero out all relevant fields
     twitter.oauth_key = None
     twitter.oauth_secret = None
     twitter.user_name = None
     #reset actions and messages
     twitter.log_messages = {}
     twitter.log_actions = []

     twitter.save()



     return {}

@must_have_permission('write')
@must_be_contributor_or_public
@must_have_addon('twitter', 'node')
def twitter_set_config(*args, **kwargs):
    """Called when settings get updated and saves input data to relevant fields
       in twitter node add-on object


        :param None

        :return: None
    """

#retrieve node add-on object
    node = kwargs.get('node') or kwargs.get('project')
    config = node.get_addon('twitter')
    twitter = kwargs['node_addon']

#building list of logs that the user wants to tweet a message for, and the messages the user has built

    twitter_logs = [k for k,v in request.json.iteritems() if v == 'on']

   # twitter_log_messages = {k:v for k,v in request.json.iteritems() if 'message' in k and v != 'None' and v != default_message}
    twitter_log_messages = {}
    for k,v in request.json.iteritems():
        if 'message' in k:
            if len(v) <= 140:
              twitter_log_messages[k]=v
            else:
              action_name = k
              twitter_log_messages[action_name] = twitter.log_messages.get(action_name)
              action_name = action_name.replace("_message", "")
              action_name = action_name.replace("_", " ")
              action_name = action_name.title()
              push_status_message("The custom message for event '"+action_name+"' is "+str(len(v) - 140)+" characters over the 140 character limit, and could not be saved.  Please use a message within the 140 character limit.", kind='warning')



#Update twitter object
    twitter.displayed_tweets  = request.json.get('displayed_tweets', '')
    twitter.log_messages= twitter_log_messages
    twitter.log_actions = twitter_logs
    twitter.save()

    return twitter.config.to_json()



@must_be_contributor_or_public
@must_have_addon('twitter', 'node')
def twitter_update_status(*args, **kwargs):
    """Called when user manually updates status
    through twitter widget

        :param None

        :return: Redirects user to settings page
    """
    node = kwargs.get('node') or kwargs.get('project')
    config = node.get_addon('twitter')

#Create twitter object
    pid = kwargs.get('pid')
    callback_url = 'http://127.0.0.1:5000/api/v1/project/'+pid+'/twitter/user_auth'
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url,  secure=True)
    auth.set_access_token(config.oauth_key, config.oauth_secret)

        #error error error

#Store status and tweet
    status = json.loads(request.data).get('status')
    try:
        send_tweet(config, status)
      #  TODO:
       # raise HTTPError(400, data={'message_long':'Your tweet was posted successfully', 'message_short':''})
    except tweepy.TweepError as e:
        if (e[0][0].get('code') == 186):
            string = 'Your tweet is too long by '+str((len(status) - 140))+ ' characters.  Please shorten it and try again.'
            raise HTTPError(400, data={'message_long': string, 'message_short': 'Twitter Error'})
        if (e[0][0].get('code') == 89):
            raise HTTPError(400, data = {'message_long' : 'Your authentication token has expired. Visit the settings page to re-authenticate.','message_short':'Twitter Error'})
            twitter.screen_name = None
            twitter.log_messages = {}
            twitter.log_actions ={}
            twitter.oauth_key = None
            twitter.oauth_secret = None
            twitter.user_name = None
            twitter.save()

    return redirect(os.path.join(node.url, 'settings'))
    return redirect('/settings/')


