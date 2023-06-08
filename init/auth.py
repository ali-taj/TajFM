import datetime

from django.utils import timezone

from init.helper import database

collection = database["auth"]

def authentication(auth_code, class_name, class_function, data_id):
    # token must have this keys
    # {
    #     "user_id": "aaaaa",
    #     "exp": "date time"
    # }
    # permission map
    # {
    #     "name": "user",
    #     "urls": {
    #         "Customer": {
    #             "get": {
    #                 "create_by": "user id",
    #                 "name": "Qoli"
    #             }
    #         },
    #         "SignUp": {
    #             "get": "all"
    #         }
    #     }
    # }
    try:
        auth_code = auth_code.split(" ")[1]
    except:
        auth_code = "not defined"

    if auth_code == "not defined":
        state_1 = class_name.__class__.__name__ == "User" and class_function in ["signup", "login", "verify"]
        state_2 = class_name.__class__.__name__ == "Product" and class_function in ["list", "get"]
        if state_1 or state_2:
            return 200
        else:
            return 403
    else:
        search_token_query = {"query": {"match_phrase": {"access.token": auth_code}}}
        search_token_count = collection.count(search_token_query)
        if search_token_count == 1:
            selected_token = collection.find(search_token_query)[0]
            now_datetime = timezone.now().timestamp()
            token_datetime = selected_token["_source"]["access"]["exp"]

            if token_datetime < now_datetime:
                return 411
            else:
                user_id = selected_token["_source"]['user_id']
                selected_user = collection.find_one(id=user_id)
                selected_permission = collection.find_one(id=selected_user["_source"]["access_level_group"])["_source"]
                if selected_permission["name"] == "admin":
                    return 200
                else:
                    auth_403 = 0
                    auth = 403

                    for permission_url in selected_permission['urls']:
                        if class_name == permission_url:
                            for permission_function in selected_permission['urls'][permission_url]:
                                if class_function == permission_function:
                                    if selected_permission['urls'][permission_url][permission_function] == "all":
                                        auth = 200
                                    else:
                                        for json_query in selected_permission['urls'][permission_url][permission_function]:
                                            auth = json_query
                                    pass
                                else:
                                    auth_403 += 1

                        else:
                            auth_403 += 1
                    if auth_403 > 0:
                        auth = 403 if auth_403 == len(selected_permission['urls']) else 200
                    if auth == 403:
                        return 403
                    elif auth == 200:
                        return 200
                    else:
                        return auth
        else:
            return 403
