import os

import openai
import json

tweets_dict = json.load(open('./BillGates_user_id_liked_tweets_dict1.pkl', 'r', encoding='UTF-8'))
openai.api_key = os.environ["OPENAI_API_KEY"]
for user_id, tweets in tweets_dict.items():
    tweets = list(map(lambda e: e.replace('\n', '').replace('\t', ''), tweets))
    prompt = 'Classify the sentiment in these tweets:\n\n'+'\n'.join([f'\"{str(i+1)}.{tweets[i]}\"'for i in range(len(tweets))])
    response = openai.Completion.create(
      model="text-davinci-002",
      prompt=prompt,
      temperature=0,
      max_tokens=60,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    print(response["choices"][0]["text"])