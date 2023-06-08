import datetime
import json
import hashlib
import random
import string

from init.helper import database, send_sms


class User:
    def __init__(self):
        self.collection = database["user"]

    def signup(self, request, url_query, auth):
        if request.headers['Content-Type'] == "application/json":
            data_string = request.rfile.read(int(request.headers['Content-Length']))
            request_data = json.loads(data_string)
            required_fields = ['user_name', 'password']
            password_fields = ['password']
            unique_fields = ['user_name', 'phone']
            for field in required_fields:
                if field not in request_data:
                    return {"response": {"BAD_REQUEST": f"field {field} does not exist in request data."},
                            "status": 400}

            for field in password_fields:
                if field in request_data:
                    request_data[field] = hashlib.sha256(str(request_data[field]).strip().encode('utf-8')).hexdigest()

            for field in unique_fields:
                if field in request_data:
                    user_exist = elastic.search(index="users", body={
                        "query": {"term": {field + ".keyword": request_data[field]}}})
                    if len(user_exist['hits']['hits']) > 0:
                        user_id = user_exist['hits']['hits'][0]["_id"]
                        if user_exist['hits']['hits'][0]["_source"]["signup_status"] == "signup":
                            return {"response": {"BAD_REQUEST": f"field {field} duplicate data found."},
                                    "status": 400}
                        else:
                            if user_exist['hits']['hits'][0]["_source"]["limit_sms_count"] < 5:
                                code = random.randint(10000, 99999)
                                user_exist['hits']['hits'][0]["_source"]["limit_sms_count"] += 1
                                request_data["code"] = code
                                request_data["limit_sms_count"] = user_exist['hits']['hits'][0]["_source"]["limit_sms_count"]
                                elastic.update(index="users", id=user_id, doc=request_data)
                                message = f'-نام سایت-\nکد اعتبارسنجی ثبت نام: {code}'
                                send_sms(message, request_data["phone"])
                                return {"response": {"SUCCESS": "code send successfully."}, "status": 200}
                            else:
                                return {"response": {
                                    "NOT_ALLOWED": "you get 5 times code. for more please contact us!"},
                                    "status": 403}

            code = random.randint(10000, 99999)
            request_data["signup_status"] = "sms"
            request_data["code"] = code
            request_data["limit_sms_count"] = 1
            request_data["access_level_group"] = "user"
            response = elastic.index(index="users", document=request_data, id=request_data["user_name"])
            return {"response": response, "status": 201}
        else:
            response = {"error": f"Content-Type {request.headers['Content-Type']} not allowed!"}
            return {"response": response, "status": 400}

    def verify(self, request, url_query, auth):
        if request.headers['Content-Type'] == "application/json":
            data_string = request.rfile.read(int(request.headers['Content-Length']))
            request_data = json.loads(data_string)
            required_fields = ['code', 'phone']

            for field in required_fields:
                if field not in request_data:
                    return {"response": {"BAD_REQUEST": f"field {field} does not exist in request data."},
                            "status": 400}
            find_user = elastic.search(index="users", body={"query": {"bool": {"must": [
                {"match_phrase": {"phone": request_data["phone"]}},
                {"match_phrase": {"code": request_data["code"]}},
            ]}}})["hits"]["hits"]
            if len(find_user) > 0:
                if find_user[0]["_source"]["signup_status"] == "signup":
                    return {"response": {"BAD_REQUEST": f"user is now signed up and don't need to verify."},
                            "status": 400}
                else:
                    update_user = elastic.update(index="users", doc={"signup_status": "signup"}, id=find_user[0]["_id"])
                    return {"response": update_user, "status": 200}
        else:
            response = {"error": f"Content-Type {request.headers['Content-Type']} not allowed!"}
            return {"response": response, "status": 400}

    def login(self, request, url_query, auth):
        if request.headers['Content-Type'] == "application/json":
            data_string = request.rfile.read(int(request.headers['Content-Length']))
            request_data = json.loads(data_string)
            password_fields = ['password']
            if 'password' not in request_data:
                return {"response": {"BAD_REQUEST": "field password does not exist in request data."},
                        "status": 400}
            if 'user_name' not in request_data:
                return {"response": {"BAD_REQUEST": "field user_name does not exist in request data."},
                        "status": 400}
            for field in password_fields:
                if field in request_data:
                    request_data[field] = hashlib.sha256(str(request_data[field]).strip().encode('utf-8')).hexdigest()

            chekc_user_exist = elastic.search(index="users", body={"query": {
                "bool": {"must": [{"match": {"user_name": request_data["user_name"]}},
                                  {"match": {"password": request_data["password"]}}]}
            }})['hits']['hits']

            if len(chekc_user_exist) > 0:
                if chekc_user_exist[0]["_source"]["signup_status"] == "signup":
                    access_token = {
                        'exp': (datetime.datetime.now() + datetime.timedelta(days=0, minutes=15)).strftime(string_time_format),
                        'token': id_generator(size=12)
                    }
                    refresh_token = {
                        'exp': (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(string_time_format),
                        'token': id_generator(size=12)
                    }

                    check_limit_login = elastic.search(index="login", body={"query": {
                        "bool": {"must": [{"match_phrase": {"user_name": request_data["user_name"]}}]}
                    }})["hits"]["hits"]
                    limit_login = 5
                    if len(check_limit_login) >= limit_login:
                        return {"response": {"NOT_ALLOWED": "login limit!"},
                                "status": 403}
                    else:
                        data = {"user_id": request_data["user_name"], "access": access_token, "refresh": refresh_token}
                        elastic.index(index="login", document=data)

                        response_login = {"access": access_token["token"],
                                          "refresh": refresh_token["token"]}
                        return {"response": response_login, "status": 200}
                else:
                    return {"response": {"NOT_ALLOWED": "user is not verified. please verify first!"},
                            "status": 403}
            else:
                return {"response": {"NOT_ALLOWED": "user not found!"},
                        "status": 403}
        else:
            response = {"error": f"Content-Type {request.headers['Content-Type']} not allowed!"}
            return {"response": response, "status": 400}

    def current_user(self, request, url_query, auth):
        auth_query = None
        if auth != 200:
            auth_query = auth
        auth_code = request.headers["Authorization"].split(" ")[1]
        login_query = {"query": {"bool": {"must": [
            {"match_phrase": {"access.token": auth_code}}
        ]}}}
        selected_login = elastic.search(index="login", body=login_query)['hits']['hits'][0]

        selected_user = elastic.get(index="users", id=selected_login["_source"]["user_id"])

        del selected_user["_source"]["code"]
        del selected_user["_source"]["limit_sms_count"]
        del selected_user["_source"]["password"]
        del selected_user["_source"]["signup_status"]
        del selected_user["_type"]
        del selected_user["_index"]
        del selected_user["_version"]
        del selected_user["_seq_no"]
        del selected_user["_primary_term"]
        return {"response": selected_user, "status": 200}

    def delete(self, request, url_query, id, auth):
        auth_query = None
        if auth != 200:
            auth_query = auth
        response = elastic.delete(index="users", id=id)
        return {"response": response, "status": 200}

    def by_id(self, request, url_query, id, auth):
        auth_query = None
        if auth != 200:
            auth_query = auth
        selected_user = elastic.get(index="users", id=id)
        del selected_user["_source"]["code"]
        del selected_user["_source"]["limit_sms_count"]
        del selected_user["_source"]["password"]
        del selected_user["_source"]["signup_status"]
        del selected_user["_type"]
        del selected_user["_index"]
        del selected_user["_version"]
        del selected_user["_seq_no"]
        del selected_user["_primary_term"]
        return {"response": selected_user, "status": 200}

    def list(self, request, url_query, auth):
        auth_query = None
        if auth != 200:
            auth_query = auth
        if "query" in url_query:
            size = url_query["query"]["size"] if "size" in url_query["query"] else 20
            page = url_query["query"]["page"] if "page" in url_query["query"] else 1
        else:
            size = 20
            page = 1
        user_list_query = {"size": size, "from": (page - 1) * size,
                           "_source": {"excludes": ["password", "limit_sms_count", "code", "signup_status"]},
                           "query": {"bool": {"must": []}}}
        if auth_query is not None:
            user_list_query["query"]["bool"]["must"].append({auth_query})
        users_list = elastic.search(index="users", body=user_list_query)['hits']['hits']
        return {"response": users_list, "status": 200}
