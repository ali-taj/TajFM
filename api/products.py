import json

from init.helper import config_data
from init.helper import elastic


class Product:
    def add(self, request, url_query, auth):
        if request.headers['Content-Type'] == "application/json":
            data_string = request.rfile.read(int(request.headers['Content-Length']))
            request_data = json.loads(data_string)
            required_fields = ['name', 'description', 'summary', 'types']
            image_fields = ['image']
            for field in required_fields:
                if field not in request_data:
                    return {"response": {"BAD_REQUEST": f"field {field} does not exist in request data."},
                            "status": 400}

            return {"response": {"add": request_data}, "status": 200}
        else:
            response = {"error": f"Content-Type {request.headers['Content-Type']} not allowed!"}
            return {"response": response, "status": 400}

    def get(self, requesr, url_query, id, auth):
        return {"response": {"get": id}, "status": 200}

    def delete(self, request, url_query, id, auth):
        response = self.users_db.remove(id)
        return {"response": response, "status": 200}

    def list(self, request, url_query, auth):
        if auth != 200:
            query = auth
        test = elastic.search(index="products", body={"query": {"match_all": {}}})
        return {"response": test, "status": 200}
