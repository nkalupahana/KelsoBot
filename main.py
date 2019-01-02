import os, sys, re, random, threading
import tweepy
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
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
search = ['Dems', 'snowflake', 'GOP', 'trump', 'shutdown'] # last keyword is time-based
apicall = 0

def getReply(text):
    global apicall
    global myStreamListener
    global natural_language_understanding

    if 39 < apicall < 80:
        print("SWITCHING TO WATSON KEY 2")
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2018-11-01',
            iam_apikey = os.getenv('WAT_KEY_2'),
            url = "https://gateway.watsonplatform.net/natural-language-understanding/api"
        )

    if 79 < apicall < 120:
        print("SWITCHING TO WATSON KEY 3")
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2018-11-01',
            iam_apikey = os.getenv('WAT_KEY_3'),
            url = "https://gateway.watsonplatform.net/natural-language-understanding/api"
        )

    if apicall > 119:
        print("API LIMITED, SHUTTING DOWN")
        print("--------------------------")
        myStreamListener.disconnect()
        sys.exit()

    try:
        apicall += 2
        response = natural_language_understanding.analyze(
        text=text,
        features=Features(entities=EntitiesOptions(sentiment=True))).get_result()
    except:
        print("Watson had trouble analyzing (1) : {}".format(text))
        return ""

    scores = [[], [], 0, 0]

    # if we found keywords in the text
    if len(response['entities']):
        # if there is a strong anger in the text
        for index, obj in enumerate(response['entities']):
            print(obj['sentiment']['score'])
            if obj['sentiment']['score'] < -0.5:
                scores[0].append(obj['sentiment']['score'])
                scores[1].append(index)

    print(scores)

    # find angriest part
    if len(scores[0]):
        for index, item in enumerate(scores[0]):
            if item < scores[2]:
                scores[3] = scores[1][index]
                scores[2] = item

        print(scores)
        print(response['entities'][scores[3]]['text'].strip())
        return response['entities'][scores[3]]['text'].strip()

    return ""

class MyStreamListener(tweepy.StreamListener):
    global myStreamListener
    global search
    global check

    def on_error(self, status_code):
        print("TWITTER ERROR " + str(status_code))
        return True

    def on_status(self, status):
        kelsoChoices = ['making a deal', 'waiting and cooling off', 'going to another game', 'talking it out', 'sharing and taking turns', 'ignoring it', 'walking away', 'telling them to stop', 'apologizing']
        openings = ['Consider', 'Try', 'I\'d suggest', 'I\'d recommend', 'I\'d start thinking about']
        start = ['Whoa!', 'Yikes!', 'Heck!', 'Dang!']
        conflictStatement = ['Don\'t get so angry at', 'It looks like you have a problem with', 'It looks like you have a conflict with', 'You\'re getting pretty mad at']

        if not status.retweeted and 'RT @' not in status.text and status.text.strip() not in check:
            myStreamListener.disconnect()
            check.append(status.text.strip())
            print(status.text.strip())
            reply = getReply(status.text.strip())

            if len(reply) and "@" not in reply:
                r1 = ""
                r2 = ""
                while r1 == r2:
                    r1 = random.choice(kelsoChoices)
                    r2 = random.choice(kelsoChoices)

                reply = "@{} {} {} {}! {} {} or {}. #kelsowheel".format(status.user.screen_name, random.choice(start), random.choice(conflictStatement), reply, random.choice(openings), r1, r2)
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', reply)
                if len(urls) > 0:
                    sleep(300)
                    return

                print(status.text)
                print(reply)
                api.update_status(status=reply, in_reply_to_status_id=status.id_str)
                sleep(300)

            myStreamListener.filter(track=search, async=True)

myStreamListener = MyStreamListener()
try:
    myStreamListener = tweepy.Stream(auth = api.auth, listener=myStreamListener)
except:
    try:
        myStreamListener.disconnect()
    except:
        pass

    sleep(300)
    myStreamListener.filter(track=search, async=True)

print(datetime.now().strftime("%H:%M %D"))
myStreamListener.filter(track=search, async=True)
