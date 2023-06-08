import requests
import pymongo

mongo_url = "mongodb://localhost:27017/"
my_client = pymongo.MongoClient(mongo_url)
database = my_client["Taj"]


smsPanelUrl = "http://smspanel.Trez.ir/SendMessageWithUrl.ashx"
smsPanelUserName = "Nowian"
smsPanelPassword = "A2980580457@"
smsPanelPhoneNumber = "50002210003000"
adminPhone = "09375908653"


def send_sms(message, phone):
    requests.get('{}?Username={}&Password={}&PhoneNumber={}&MessageBody={}&RecNumber={}&Smsclass=1'
                 .format(smsPanelUrl, smsPanelUserName, smsPanelPassword, smsPanelPhoneNumber, message, phone))
