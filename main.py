import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser

from init.urls import valid_urls
# import socketserver

from init.auth import authentication

hostName = "127.0.0.1"
serverPort = 8080
UI_port = 8081


class MyServer(BaseHTTPRequestHandler):

    def _set_headers(self, status):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def main(self, request):
        url_path = request.path
        query_dictionary = {}
        if "?" in url_path:
            for key in url_path.split("/?")[1].split("&"):
                query_dictionary[key.split("=")[0].strip()] = key.split("=")[1].split(",")
            url_path = url_path.split("/?")[0]

        url = url_path.split("/")[1]

        if url not in valid_urls:
            response = {"NOT_FOUND": f"url '{url}' not found!"}
            request._set_headers(404)
            request.wfile.write(json.dumps(response).encode(encoding='utf_8'))
        else:
            class_name = valid_urls[url]()
            class_function = url_path.split("/")[2] if len(url_path.split("/")) > 2 else None
            data_id = url_path.split("/")[3] if len(url_path.split("/")) > 3 else None
            inefficient_data = url_path.split("/")[4] if len(url_path.split("/")) > 4 else None
            if inefficient_data is not None:
                response = {"KEY_ERROR": inefficient_data}
                request._set_headers(400)
                request.wfile.write(json.dumps(response).encode(encoding='utf_8'))
            else:
                auth_code = self.headers["Authorization"]
                auth_result = authentication(auth_code, class_name, class_function, data_id)

                if auth_result == 403:
                    request._set_headers(403)
                    request.wfile.write(
                        json.dumps({"error": "you don't have permissions for this request!"}).encode(encoding='utf_8'))
                elif auth_result == 411:
                    request._set_headers(403)
                    request.wfile.write(
                        json.dumps({"error": "token is expired!"}).encode(encoding='utf_8'))
                else:
                    # try:
                    if class_function is not None:
                        call_able_function = eval("class_name." + class_function)

                    else:
                        call_able_function = eval("class_name")()

                    if data_id is not None and data_id != "":
                        api_response = call_able_function(request=request, url_query=query_dictionary, id=data_id, auth=auth_result)
                    else:
                        api_response = call_able_function(request=request, url_query=query_dictionary, auth=auth_result)

                    request._set_headers(api_response["status"])
                    request.wfile.write(json.dumps(api_response["response"]).encode(encoding='utf_8'))

                # except AttributeError as e:
                #     response = {"BAD_REQUEST": f"{class_function} is not allowed in {class_name}."}
                #     request._set_headers(400)
                #     request.wfile.write(json.dumps(response).encode(encoding='utf_8'))
                # except Exception as e:
                #     response = {"BAD_REQUEST": str(e)}
                #     request._set_headers(400)
                #     request.wfile.write(json.dumps(response).encode(encoding='utf_8'))

    def do_GET(self):
        self.main(self)

    def do_POST(self):
        self.main(self)


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    # webServer.socket = ssl.wrap_socket(
    #     webServer.socket,
    #     keyfile="path/to/key.pem",
    #     certfile='path/to/cert.pem',
    #     server_side=True)

    try:
        webServer.serve_forever()
    except:
        pass

# return html sample
#         try:
#             fname, ext = os.path.splitext(self.path)
#             if ext in (".html",):
#                 # with open(curdir + sep + "site" + self.path, 'rb') as f:
#                 html_file = open("site/" + self.path, "r", encoding="utf-8").read()
#                 self.send_response(200)
#                 self.send_header('Content-type', types_map[ext])
#                 self.end_headers()
#                 self.wfile.write(html_file.format("ali").encode("utf-8"))
#
#             elif ext in (".css", ".js", ".jpg", ".svg", ".png", "jpeg"):
#                 with open(curdir + sep + "site" + self.path, 'rb') as f:
#                     self.send_response(200)
#                     self.send_header('Content-type', types_map[ext])
#                     self.end_headers()
#                     self.wfile.write(f.read())
#             elif ext in (".woff", ".ttf", ".eot"):
#                 fonts_mime_types = {".woff": "font/woff", ".ttf": "application/octet-stream",
#                                     ".eot": "application/vnd.ms-fontobject"}
#                 with open(curdir + sep + "site" + self.path, 'rb') as f:
#                     self.send_response(200)
#                     self.send_header('Content-type', fonts_mime_types[ext])
#                     self.end_headers()
#                     self.wfile.write(f.read())
#             return
#         except IOError:
#             self.send_error(404)
