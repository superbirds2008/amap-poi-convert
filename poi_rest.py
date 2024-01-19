import typer
import csv
import requests
from typing import List, Tuple
from fastapi import FastAPI, UploadFile, File
app = typer.Typer()
api = FastAPI()

def get_location(address: str, api_key: str) -> str:
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {"address": address, "output": "JSON", "key": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        return response.json()["geocodes"][0].get("location", "")
    else:
        print(f"Error: {response.status_code} - {response.json().get('info', '')}")
    return ""

def get_pois(location: str, api_key: str) -> List[Tuple[str, str]]:
    url = "https://restapi.amap.com/v3/geocode/regeo"
    params = {"location": location, "output": "JSON", "key": api_key, "extensions": "all"}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        return [(poi["id"], poi["name"]) for poi in response.json()["regeocode"]["pois"]]
    else:
        print(f"Error: {response.status_code} - {response.json().get('info', '')}")
    return []

@api.post("/process_csv")
async def process_csv(input_file: UploadFile = File(...), 
                      api_key: str = "e813774a4aea1a0b6ca95f16bcd36cd4", 
                      start_line: int = 0, 
                      end_line: int = 0 
                      ):
    """
    处理一个包含地址的CSV文件，使用高德地图的AMap API获取它们的位置，并将相应的兴趣点（POIs）写入输出的CSV文件。
    高德地图免费API申请地址：https://lbs.amap.com/dev/key/app，添加的API类型为Web服务-Web服务API。
    该API每天有5000次的免费调用次数，超过后会返回错误信息。
    本程序每查询一个地址，就会消耗一次调用次数，所以请谨慎使用。
    
    参数:
    """
    with open(input_file.filename, mode='r', encoding='utf-8') as infile:
        #如果end_line==0，那么就是到最后一行
        if end_line == 0:
            end_line = sum(1 for line in infile)
    with open(input_file.filename, mode='r', encoding='utf-8') as infile, \
         open("output.csv", mode='w', encoding='utf-8', newline='') as outfile:

       #如果start_line==0，那么就是从第一行开始
        if start_line > 0:
            start_line = start_line - 1
        
        print(f'处理文件{input_file.filename}的{start_line + 1:4d}到{end_line:4d}行的数据')
             
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for i, row in enumerate(reader):
            print(f'查询第{i+1:4d}行的地址: {row[0]}')
            if start_line <= i < end_line:
                address = row[0]
                location = get_location(address, api_key)
                if location:
                    pois = get_pois(location, api_key)
                    for poi_id, poi_name in pois:
                        writer.writerow([address, poi_id, poi_name])

if __name__ == "__main__":
    app()
