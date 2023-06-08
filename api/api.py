import base64
import requests

from init.helper import database


class Chat:

    def chat_id(self, request, auth, url_query):
        return {"response": url_query, "status": 200}


class DKProducts:

    def __init__(self):
        self.collection = database["products"]

    def get(self, request, auth):

        active_count = 0
        product_list = self.collection.list()
        for data in product_list:
            if "status" in data:
                if data["status"] == "marketable":
                    active_count += 1
        response = {"gender Male Count": active_count, "all_count": len(product_list)}
        return {"response": response, "status": 200}

    def get_dg_product(self, request, auth):
        for i in range(109204, 9000000):
            url = f"https://api.digikala.com/v1/product/{i}/"
            url_request = requests.get(url).json()
            if "data" in url_request:
                product_data = url_request["data"]["product"]
                if "is_inactive" not in product_data and product_data["status"] == "marketable":
                    dk_base64_url = base64.b64encode(bytes(f'https://www.digikala.com/product/dkp-{i}', 'utf-8'))
                    main_affiliate_url = "https://affstat.adro.co/click/1eea7fa4-ee12-435b-958c-e4727a721a7e/"
                    data_for_save = {"id": product_data["id"],
                                     "dk_url": "https://www.digikala.com{}".format(product_data["url"]["uri"]),
                                     "affilator_url": f"{main_affiliate_url}{dk_base64_url}"}
        return {"response": f"{i} products created!", "status": 201}
