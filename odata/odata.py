import os
import requests
import json
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any

def odata_verify(
         results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

      if os.getenv("VERIFY_FLAG") == "true":
        # OData 服务URL
        url = os.getenv("ODATA_URL")
        # 身份验证信息
        username = os.getenv("ODATA_USER")
        password = os.getenv("ODATA_PASSWORD")

        # 设置请求头
        headers = {
           "Content-Type": "application/json",
           "Accept": "application/json",
           "x-csrf-token": "Fetch"  # 首先获取CSRF令牌
        }

        # 获取CSRF令牌
        session = requests.Session()
        csrf_response = session.get(
         url,
         auth=HTTPBasicAuth(username, password),
         headers=headers
        )

        # 从响应头中提取CSRF令牌
        csrf_token = csrf_response.headers.get('x-csrf-token', '')
        headers['x-csrf-token'] = csrf_token

        # 初始化结果列表
        item_field_list = []

        # 遍历 match_result 并生成所需的结构
        for i, result in enumerate(results, start=1):
            if result["table_id"] and result["table_id"] != "":
              item_field = {
                "TabFdPos": str(i),
                "ToEntity": result["table_id"],
                "ToField": result["field_id"]
              }
              item_field_list.append(item_field)

        # 生成最终的 JSON 结构
        request_json = {
            "_ItemField": item_field_list
        }
        
        # 发起POST请求
        response = session.post(
            url,
            # auth=HTTPBasicAuth(username, password),
            headers=headers,
            data=json.dumps(request_json)
        )

        # 打印结果
        if response.status_code == 201:  # 201表示成功
            checkresults = response.json().get("_ItemField", "")
            
            # 将 checkresults 转换为字典，以便快速查找
            checkresults_dict = {(item["ToEntity"], item["ToField"]): item for item in checkresults}
            for result in results:
               key = (result["table_id"], result["field_id"])
               if key in checkresults_dict:
                  checkresult = checkresults_dict[key]
                  if checkresult["ReturnCode"] == 0:
                    result["verify"] = "√"
                  else:
                    result["table_id"] = ""
                    result["field_id"] = ""
                    result["data_type"] = ""
                    result["length_total"] = ""
                    result["length_dec"] = ""
                    result["sample_value"] = ""
                    result["match"] = ""
                    result["notes"] = os.getenv("ODATA_MESSAGE") 
                    # result["verify"] = checkresult["ReturnMessage"]
               else:
                 result["verify"] = "-"
        else:
           print(f"错误: {response.text}")
      return results