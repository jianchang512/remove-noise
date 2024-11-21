import requests

res=requests.post('http://127.0.0.1:5080/api',data={"stream":1},files={"audio":open('./300.wav','rb')})

if res.status_code!=200:
    print(res.text)
    exit()

with open("ceshi.wav",'wb') as f:
    f.write(res.content)
    
    
    