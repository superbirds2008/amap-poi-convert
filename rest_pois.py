from fastapi.responses import FileResponse, HTMLResponse
import typer
import csv
import requests
from typing import List, Tuple
from fastapi import FastAPI, UploadFile, File, APIRouter
from uvicorn import Config, Server
import asyncio
import argparse
from fastapi import Request
app = typer.Typer()
router = APIRouter()
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

#生成下面函数的测试curl命令：
#curl -X POST "http://127.0.0.1:8123/api/v1/process_csv" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "input_file=@input.csv"
@router.post("/process_csv")
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
        #把生成的output.csv文件返回给调用者
        # return FileResponse("output.csv")
        #把生成的结果以output.csv的文件名返回给调用者
        return FileResponse("output.csv", filename="result.csv")

#生成一个简单的web页面，用于上传文件，submit按钮调用上面的process_csv函数
#美化布局下面的HTML页面，标题为“高德地图POI批量转换工具”，居中显示，字体大小为24px；两个按钮也居中显示，字体大小为18px；上传文件的按钮宽度为200px，高度为50px，字体大小为18px；submit按钮宽度为100px，高度为30px，字体大小为18px。
#加入两个示例表格，分别为input.csv和output.csv，用于测试上传文件和下载文件功能。
@router.get("/upload")
async def upload(request: Request):
    base_url = str(request.base_url)
    process_csv_url = request.url_for("process_csv")
    print(base_url)
    content1 = """
    <html>
        <head>
            <title>高德地图POI批量转换工具</title>
            <style>
                body {
                    text-align: center;
                }
                h1 {
                    font-size: 24px;
                }
                button {
                    font-size: 18px;
                }
                input[type="file"] {
                    width: 200px;
                    height: 50px;
                    font-size: 18px;
                }
                input[type="submit"] {
                    width: 100px;
                    height: 30px;
                    font-size: 18px;
                }
                table {
                    margin: auto;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        """
    content = content1 + f"""
        <body>
            <h1>高德地图批量查询POI工具</h1>
            <form action="{process_csv_url}" enctype="multipart/form-data" method="post">
                <input name="input_file" type="file" multiple>
                <input type="submit">
            </form>
           <h2>上传csv格式文件示例</h2>
            <table border="1">
                <tr>
                    <td>上海市中华艺术宫</td>
                </tr>
                <tr>
                    <td>北京清华大学</td>
                </tr>
                <tr>
                    <td>河北省张家口市崇礼区万龙滑雪场</td>
                </tr>
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--host", '-H', type=str,
                        default="0.0.0.0", help="Host IP address")
    parser.add_argument("--port", '-P', type=int,
                        default=8341, help="Port number")
    args = parser.parse_args()
    rest_app = FastAPI()
    loop = asyncio.get_event_loop()
    rest_app.include_router(router,
                       prefix="/api/v1",
                       tags=["api"],
                       responses={404: {"description": "Not found"}})
    server = Server(Config(app=rest_app,
                           loop=loop,
                           port=args.port,
                           host=args.host,
                        ))
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    main()
