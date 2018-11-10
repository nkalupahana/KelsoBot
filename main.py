import tweepy
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
import threading
import random
import os
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions

load_dotenv()

auth = tweepy.OAuthHandler(os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET'))
auth.set_access_token(os.getenv('ACCESS_TOKEN'), os.getenv('ACCESS_SECRET'))
api = tweepy.API(auth)

natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2018-11-01',
    iam_apikey = os.getenv('WAT_KEY'),
    url = "https://gateway.watsonplatform.net/natural-language-understanding/api"
)

check = []
search = ['Dems', 'snowflake', 'GOP', 'trump', 'vote']
apicall = 0

def getReply(text):
    if apicall > 39:
        sleep(60)
        return ""
    try:
        apicall += 2
        response = natural_language_understanding.analyze(
        text=text,
        features=Features(entities=EntitiesOptions(sentiment=True))).get_result()
    except:
        print("Watson had trouble analyzing (1) : {}".format(text))
        return ""

    # if we found keywords in the text
    if len(response['entities']):
        # if there is a strong anger in the text
        for obj in response['entities']:
            if obj['sentiment']['score'] < -0.3:
                return obj['text'].strip()

    return ""

class MyStreamListener(tweepy.StreamListener):
    global myStreamListener
    global search

    def on_status(self, status):
        kelsoChoices = ['making a deal', 'waiting and cooling off', 'going to another game', 'talking it out', 'sharing and taking turns', 'ignoring it', 'walking away', 'telling them to stop', 'apologizing']
        openings = ['Consider', 'Try', 'I\'d suggest', 'I\'d recommend', 'I\'d start thinking about']
        start = ['Whoa!', 'Yikes!', 'Heck!', 'Dang!']
        conflictStatement = ['Don\'t get so angry at', 'It looks like you have a problem with', 'It looks like you have a conflict with', 'You\'re getting pretty mad at']

        if not status.retweeted and 'RT @' not in status.text and status.text.strip() not in check:
            myStreamListener.disconnect()
            print(status.text)
            check.append(status.text.strip())
            reply = getReply(status.text.strip())
            if len(reply):
                r1 = ""
                r2 = ""
                while r1 == r2:
                    r1 = random.choice(kelsoChoices)
                    r2 = random.choice(kelsoChoices)

                reply = "@{} {} {} {}! {} {} or {}. #kelsowheel".format(status.user.screen_name, random.choice(start), random.choice(conflictStatement), reply, random.choice(openings), r1, r2)
                print(reply)
                api.update_status(status=reply, in_reply_to_status_id=status.id_str)
                sleep(300)

            myStreamListener.filter(track=search, async_=True)


myStreamListener = MyStreamListener()
myStreamListener = tweepy.Stream(auth = api.auth, listener=myStreamListener)

myStreamListener.filter(track=search, async_=True)

def apiManager():
    global apicall
    hour = datetime.now()

    if hour is not datetime.now().hour:
        apicall = 0
        hour = datetime.now().hour

t = threading.Thread(target=apiManager)
t.daemon = True
t.start()

while True:
    stayalive = True
