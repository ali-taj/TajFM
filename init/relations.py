import datetime

from init.helper import elastic


def relation_controller(**kwargs):
    # relation_document = {
    #     "target_index": ,
    #     "target_field": ,  # "field1.object.object"
    #     "target_id": ,
    #     "base_index": ,
    #     "base_id":  # ["field1", "field2.object"]
    # }

    target_field_list = kwargs['target_field'].split(".")
    field_object_index = 0
    all_fields_index = ""

    selected_document = elastic.get(index=kwargs["target_index"], id=kwargs["target_id"])["_source"]

    for field_object in target_field_list:

        if "FK" in field_object:
            fk_id = field_object.split("::")[1]

            for obj in eval('selected_document' + all_fields_index):
                if fk_id in obj.values():
                    all_fields_index += "[" + str(eval('selected_document' + all_fields_index).index(obj)) + "]"
        else:
            all_fields_index += "['" + field_object + "']"
        field_object_index += 1

    if kwargs["base_index"] == "dataset":
        base_data = []
        for base_id in kwargs["base_id"]:
            base_index_fields = {"id": base_id,
                                 "relation_index": kwargs["base_index"],
                                 "labels": kwargs["base_id"][base_id]}
            base_data.append(base_index_fields)

    else:
        base_data = []
        for base_id in kwargs["base_id"]:
            base_index_fields = {"id": base_id,
                                 "relation_index": kwargs["base_index"]}
            base_data.append(base_index_fields)
    exec('selected_document' + all_fields_index + '=base_data')
    update_data_to_target = elastic.index(index=kwargs["target_index"], id=kwargs["target_id"],
                                          document=selected_document)

    if "FK" in kwargs["target_field"]:
        inner_field = kwargs["target_field"].split(".")[-1]
        field = kwargs["target_field"].split(".")[0]
        inner_FK = f"{field}.FK::{inner_field}"
    else:
        inner_FK = kwargs["target_field"]

    check_relation_in_duplicate = elastic.count(index="index_relations", body={"query": {"bool": {
        "must": [{"match_phrase": {"target_index": kwargs["target_index"]}},
                 {"match_phrase": {"target_field": inner_FK}},
                 {"match_phrase": {"base_index": kwargs["base_index"]}}]
    }}})['count']
    if check_relation_in_duplicate == 0:
        relation_document = {
            "target_index": kwargs["target_index"],
            "target_field": inner_FK,
            "base_index": kwargs["base_index"]
        }
        elastic.index(index="index_relations", document=relation_document)

    return update_data_to_target


def append_data(data):
    document = elastic.get(index=data["relation_index"], id=data["id"])
    del document["_index"]
    del document["found"]
    del document["_seq_no"]
    del document["_primary_term"]
    del document["_version"]

    return document


def main_connector_function(all_fields_index, item):
    try:
        relation_dict_index = 0
        if "_source" in item:
            for relation_dict in eval("item['_source']" + all_fields_index):

                must_append_data = append_data(eval("item['_source']" + all_fields_index + "[relation_dict_index]"))
                try:

                    relation_connector(must_append_data,
                                       eval("item['_source']" + all_fields_index + "[relation_dict_index]")[
                                           "relation_index"])
                except Exception as e:
                    pass
                del eval("item['_source']" + all_fields_index + "[relation_dict_index]")["id"]
                del eval("item['_source']" + all_fields_index + "[relation_dict_index]")["relation_index"]

                for f in must_append_data:
                    eval("item['_source']" + all_fields_index + "[relation_dict_index]")[f] = must_append_data[f]

                relation_dict_index += 1
        else:
            for relation_dict in eval("item" + all_fields_index):

                must_append_data = append_data(eval("item" + all_fields_index + "[relation_dict_index]"))
                try:

                    relation_connector(must_append_data,
                                       eval("item" + all_fields_index + "[relation_dict_index]")[
                                           "relation_index"])
                except Exception as e:
                    pass
                del eval("item" + all_fields_index + "[relation_dict_index]")["id"]
                del eval("item" + all_fields_index + "[relation_dict_index]")["relation_index"]

                for f in must_append_data:
                    eval("item" + all_fields_index + "[relation_dict_index]")[f] = must_append_data[f]

                relation_dict_index += 1

    except KeyError as e:
        pass
    except IndexError as e:
        pass
    except Exception as e:
        pass


def relation_connector(data, index):
    all_relations = elastic.search(index="index_relations",
                                                body={"size": 500, "query": {"match_phrase": {
                                                    "target_index": index}}})['hits']['hits']

    if len(all_relations) > 0:
        for relation in all_relations:
            # check item is in data or not (main data or sub data)
            if "items" in data:
                for item in data['items']:
                    target_field_list = relation["_source"]['target_field'].split(".")
                    all_fields_index_list = [""]
                    all_fields_index_list_number = 0
                    all_fields_index = ""
                    selected_document = item["_source"]
                    for field_object in target_field_list:
                        appended_fk = []
                        if "FK" in field_object:
                            fk_id = field_object.split("::")[1]

                            try:
                                obj_index_number = 0
                                for obj in eval(
                                        'selected_document' + all_fields_index_list[all_fields_index_list_number]):
                                    if fk_id in obj.keys():
                                        appended_fk.append("[" + str(obj_index_number) + "]" + "['" + fk_id + "']")
                                    obj_index_number += 1

                            except Exception as e:
                                pass
                        fk_loop_index = 0
                        for index_object in all_fields_index_list:
                            if len(appended_fk) > 0:
                                if fk_loop_index < len(appended_fk):
                                    pre_data = index_object
                                    all_fields_index_list.pop(all_fields_index_list.index(index_object))
                                    all_fields_index_list_number -= 1
                                    for fk in appended_fk:
                                        all_fields_index_list.append(pre_data + fk)
                                        all_fields_index_list_number += 1
                                        fk_loop_index += 1
                            else:
                                all_fields_index_list[
                                    all_fields_index_list.index(index_object)] += "['" + field_object + "']"
                    for fields_index in all_fields_index_list:
                        # 1
                        main_connector_function(fields_index, item)

            else:
                target_field_list = relation["_source"]['target_field'].split(".")
                all_fields_index_list = [""]
                all_fields_index_list_number = 0
                all_fields_index = ""
                if "_source" in data:
                    selected_document = data["_source"]
                else:
                    selected_document = data
                for field_object in target_field_list:
                    appended_fk = []
                    if "FK" in field_object:
                        fk_id = field_object.split("::")[1]

                        try:
                            obj_index_number = 0
                            for obj in eval('selected_document' + all_fields_index_list[all_fields_index_list_number]):
                                if fk_id in obj.keys():
                                    appended_fk.append("[" + str(obj_index_number) + "]" + "['" + fk_id + "']")
                                obj_index_number += 1

                        except Exception as e:
                            pass
                    fk_loop_index = 0
                    for index_object in all_fields_index_list:
                        if len(appended_fk) > 0:
                            if fk_loop_index < len(appended_fk):
                                pre_data = index_object
                                all_fields_index_list.pop(all_fields_index_list.index(index_object))
                                all_fields_index_list_number -= 1
                                for fk in appended_fk:
                                    all_fields_index_list.append(pre_data + fk)
                                    all_fields_index_list_number += 1
                                    fk_loop_index += 1
                        else:
                            all_fields_index_list[
                                all_fields_index_list.index(index_object)] += "['" + field_object + "']"
                for fields_index in all_fields_index_list:
                    # 2
                    main_connector_function(fields_index, data)
    return data


def delete_data(base_index, delete_doc_id):
    all_rel_query = {"query": {"match_phrase": {"base_index": base_index}}}
    all_relations = elastic.search(index="index_relations", body=all_rel_query)['hits']['hits']
    s = {"target_index": "insta_posts",
         "target_field": "damage.fajr_tak_zan_chador",
         "base_index": "fajrc_labels"}
    if len(all_relations) > 0:
        for relation in all_relations:
            find_relation_query = {"query": {"bool": {"must": [
                {"term": {relation["target_field"] + ".id.keyword": delete_doc_id}}]}},
                "script": {
                    "source": "const list = ctx._source.{}; for (let i = 0; i < list.length; i++) {if (list[i].id == {}) {ctx._source.remove('{}[i]')}".format(
                        relation['target_field'], delete_doc_id, relation['target_field'])}}
            update_all_documents = elastic.update_by_query(index=relation["target_index"],
                                                           body=find_relation_query)
            delete_doc = {"delete_status": True, "update_time": datetime.datetime.now()}
            update_delete_item = elastic.update(index=relation["base_index"],
                                                id=delete_doc_id, doc=delete_doc)
            return {"document delete status": update_delete_item, "relations delete status": update_all_documents}


def add_log(operations_index, operation_name, operation_user, operated_id, pre_value=None, new_value=None):
    document = {
        "index": operations_index,
        "operation": operation_name,
        "user": operation_user,
        "operated_document_id": operated_id,
        "create_date": datetime.datetime.now(),
    }

    if pre_value is not None:
        document["pre_value"] = pre_value
    if new_value is not None:
        document["new_value"] = new_value

    add_log_data = elastic.index(index="log", document=document)

    return add_log_data
